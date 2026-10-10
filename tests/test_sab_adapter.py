"""SAB adapter tests with a synthetic mini-benchmark (no real SAB data)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from verifront.sab.adapter import (
    SabTaskPaths,
    build_task_spec,
    parse_eval_line,
    prepare_workdir,
    run_eval,
)


@pytest.fixture()
def mini_benchmark(tmp_path):
    """benchmark/eval_programs/eval_toy.py compares pred vs gold CSV."""
    bench = tmp_path / "benchroot" / "benchmark"
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


def test_prepare_workdir_layout(mini_benchmark, tmp_path):
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd")
    prepare_workdir(paths)
    assert (paths.workdir / "benchmark").is_symlink()
    assert (paths.workdir / "benchmark" / "eval_programs" / "eval_toy.py").is_file()
    assert (paths.workdir / "pred_results").is_dir()


def test_end_to_end_toy_task(mini_benchmark, tmp_path):
    paths = SabTaskPaths(benchmark_root=mini_benchmark, workdir=tmp_path / "wd")
    prepare_workdir(paths)
    spec = build_task_spec(
        {"task_inst": "Write 7 to pred.csv", "domain_knowledge": "none",
         "dataset_folder_tree": "-- data/", "dataset_preview": "empty",
         "output_fname": "pred_results/pred.csv"},
        999,
    )
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
