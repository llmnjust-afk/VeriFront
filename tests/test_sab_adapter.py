"""SAB adapter tests with a synthetic mini-benchmark (no real SAB data)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from verifront.sab.adapter import (
    SabTaskPaths,
    build_task_spec,
    chown_workdir,
    parse_eval_line,
    prepare_workdir,
    run_eval,
)


@pytest.fixture()
def mini_benchmark(tmp_path):
    """benchmark/eval_programs/eval_toy.py compares pred vs gold CSV."""
    bench = tmp_path / "benchroot" / "benchmark"
    (bench / "datasets" / "toydata").mkdir(parents=True)
    (bench / "datasets" / "toydata" / "data.csv").write_text("x\n1\n", encoding="utf-8")
    (bench / "eval_programs" / "gold_results").mkdir(parents=True)
    (bench / "eval_programs" / "eval_toy.py").write_text(
        "import pandas as pd\n"
        "def eval():\n"
        "    pred = pd.read_csv('./pred_results/pred.csv')\n"
        "    gold = pd.read_csv('./benchmark/eval_programs/gold_results/gold.csv')\n"
        "    ok = int((pred['v'] == gold['v']).all())\n"
        "    return ok, f'{ok} / 1'\n"
        "print(eval())\n",
        encoding="utf-8",
    )
    (bench / "eval_programs" / "gold_results" / "gold.csv").write_text("v\n7\n", encoding="utf-8")
    return bench.parent


class ScriptedClient:
    model = "fake"
    snapshot = "fake-snap"

    def __init__(self, responses):
        self.responses = list(responses)

    def chat(self, messages, temperature=0.0, max_tokens=1024, seed=None):
        return {
            "content": self.responses.pop(0),
            "token_usage": {"prompt": 5, "completion": 2},
            "model": self.model,
            "latency_s": 0.0,
            "raw": {},
        }


def test_parse_eval_line():
    assert parse_eval_line("(1, '5 / 5')") == (1, "5 / 5")
    assert parse_eval_line("(0, 'N/A')") == (0, "N/A")
    assert parse_eval_line("garbage") is None


ROW = {
    "task_inst": "Write 7 to pred.csv",
    "domain_knowledge": "none",
    "dataset_folder_tree": "|-- toydata/\n| |---- data.csv",
    "dataset_preview": "empty",
    "output_fname": "pred_results/pred.csv",
}


def test_prepare_workdir_layout(mini_benchmark, tmp_path):
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd")
    prepare_workdir(paths, ROW)
    # Official agent view: dataset dir copied as REAL files; NO benchmark link.
    assert (paths.workdir / "toydata" / "data.csv").is_file()
    assert not (paths.workdir / "toydata" / "data.csv").is_symlink()
    assert not (paths.workdir / "benchmark").exists()
    assert (paths.workdir / "pred_results").is_dir()


def test_agent_cannot_see_protected_dirs(mini_benchmark, tmp_path):
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd")
    prepare_workdir(paths, ROW)
    import os as _os
    listing = sorted(_os.listdir(paths.workdir))
    assert listing == ["pred_results", "toydata"], listing


def test_dataset_names_from_row():
    from verifront.sab.adapter import dataset_names_from_row
    assert dataset_names_from_row(ROW) == ["toydata"]
    assert dataset_names_from_row({"dataset_folder_tree": ""}) == []


def test_eval_swaps_in_full_tree(mini_benchmark, tmp_path):
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd")
    prepare_workdir(paths, ROW)
    (paths.workdir / "pred_results" / "pred.csv").write_text("v\n7\n", encoding="utf-8")
    ev = run_eval(paths, "eval_toy.py", "python3")
    assert ev["success"] == 1, ev
    # After eval the workdir benchmark is the full tree (eval-time requirement).
    assert (paths.workdir / "benchmark" / "eval_programs" / "eval_toy.py").is_file()


def test_sandbox_cmd_and_env(tmp_path):
    from verifront.agents.codeact import CodeActAgent, CodeActConfig
    cfg = CodeActConfig(sandbox=True, python_bin="python3")
    agent = CodeActAgent(None, cfg, workdir=tmp_path)
    cmd = agent._unshare_cmd(tmp_path / "step_01.py")
    assert cmd[0] == "unshare" and "mount --bind" in cmd[4]
    os.environ["FRONTIER_API_KEY"] = "leak-test"
    try:
        env = agent._sandbox_env()
        assert "FRONTIER_API_KEY" not in env
    finally:
        os.environ.pop("FRONTIER_API_KEY", None)


def _chmod_traverse(path: Path) -> None:
    """Make the parent chain traversable (o+x) for the nobody sandbox tests."""
    p = path.resolve()
    while p != Path("/tmp") and p != p.parent:
        try:
            os.chmod(p, 0o751)
        except OSError:
            pass
        p = p.parent


def test_end_to_end_sandboxed_step(mini_benchmark, tmp_path):
    """Full loop with sandbox on: agent code must NOT see /data/lab or env key."""
    if os.geteuid() != 0:
        pytest.skip("nobody drop requires root")
    _chmod_traverse(tmp_path)
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd")
    prepare_workdir(paths, ROW)
    chown_workdir(paths)
    probe = (
        "import os, json\n"
        "try:\n"
        "    os.listdir('/data/lab')\n"
        "    lab_hidden = False\n"
        "except PermissionError:\n"
        "    lab_hidden = True\n"
        "info = {\n"
        "  'cwd': os.getcwd(),\n"
        "  'euid': os.geteuid(),\n"
        "  'key_leak': os.environ.get('FRONTIER_API_KEY'),\n"
        "  'lab_hidden': lab_hidden,\n"
        "  'listing': sorted(os.listdir('.')),\n"
        "}\n"
        "open('pred_results/probe.json','w').write(json.dumps(info))\n"
        "print('probed')\n"
    )
    client = ScriptedClient([f"<code>{probe}</code>", "<final>done</final>"])
    from verifront.agents.codeact import CodeActAgent, CodeActConfig as _CC

    agent = CodeActAgent(client, _CC(max_steps=2, step_timeout_s=30,
                                     python_bin="python3", sandbox=True),
                         workdir=paths.workdir, agent_commit="test")
    run = agent.run(build_task_spec(ROW, 999))
    probe_out = json.loads((paths.workdir / "pred_results" / "probe.json").read_text())
    assert probe_out["key_leak"] is None
    assert probe_out["lab_hidden"] is True
    assert probe_out["listing"] == ["pred_results", "step_01.py", "toydata"]
    assert run.status == "completed"


def test_end_to_end_toy_task(mini_benchmark, tmp_path):
    if os.geteuid() == 0:
        _chmod_traverse(tmp_path)
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd")
    prepare_workdir(paths, ROW)
    chown_workdir(paths)
    spec = build_task_spec(ROW, 999)
    client = ScriptedClient([
        "<code>import os; os.makedirs('pred_results', exist_ok=True)\n"
        "open('pred_results/pred.csv','w').write('v\\n7\\n')</code>",
        "<final>wrote the file</final>",
    ])
    from verifront.agents.codeact import CodeActAgent, CodeActConfig

    agent = CodeActAgent(client, CodeActConfig(max_steps=2, step_timeout_s=10,
                                               python_bin="python3"),
                         workdir=paths.workdir, agent_commit="test")
    run = agent.run(spec)
    assert run.status == "completed"
    ev = run_eval(paths, "eval_toy.py", "python3")
    assert ev["success"] == 1, ev
    assert ev["detail"] == "1 / 1"
    assert run.trajectory is not None and run.trajectory.validate() == []


def test_eval_missing_script_raises(mini_benchmark, tmp_path):
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd2")
    prepare_workdir(paths)
    with pytest.raises(FileNotFoundError):
        run_eval(paths, "nope.py", "python3")
