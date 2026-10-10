"""Run one SAB task end-to-end: agent -> official eval -> result artifacts.

  python scripts/run_sab_task.py --instance-id 29 --arm frontier \
      [--config configs/models.yaml] [--python-bin .../testbed/bin/python]

Artifacts under runs/sab_<id>/<arm>/<ts>/: trace.jsonl, result.json (tokens,
wall time, eval verdict). run dirs are gitignored.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verifront.agents.base import load_models_config  # noqa: E402
from verifront.agents.codeact import CodeActConfig, client_from_config  # noqa: E402
from verifront.sab.adapter import (  # noqa: E402
    SabTaskPaths,
    build_task_spec,
    get_task,
    load_verified_tasks,
    prepare_workdir,
    run_codeact,
    run_eval,
)

BENCHMARK_ROOT_DEFAULT = Path("/data/lab/sab_data/benchmark_verified")
PARQUET_DEFAULT = Path("/data/lab/sab_data/verified.parquet")
PYTHON_BIN_DEFAULT = "/root/.local/share/mamba/envs/testbed/bin/python"


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT),
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance-id", type=int, required=True)
    ap.add_argument("--arm", default="frontier")
    ap.add_argument("--config", default=str(ROOT / "configs/models.yaml"))
    ap.add_argument("--parquet", default=str(PARQUET_DEFAULT))
    ap.add_argument("--benchmark-root", default=str(BENCHMARK_ROOT_DEFAULT))
    ap.add_argument("--workdir-root", default=str(ROOT / "runs"))
    ap.add_argument("--python-bin", default=PYTHON_BIN_DEFAULT)
    ap.add_argument("--max-steps", type=int, default=12,
                    help="frozen P1 budget (configs/sampling_p1.yaml)")
    ap.add_argument("--step-timeout", type=float, default=300.0)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--hint", default="",
                    help="anchor hint (single clause) appended as extra_rules; "
                         "runs go under <arm>_<label> with label='hint'")
    args = ap.parse_args()

    label = "hint" if args.hint else ""
    arm_dir = args.arm + (f"_{label}" if label else "")
    cfg = load_models_config(args.config)
    df = load_verified_tasks(args.parquet)
    row = get_task(df, args.instance_id)
    eval_script = str(row["eval_script_name"])

    task_dir = Path(args.workdir_root) / f"sab_{args.instance_id}" / arm_dir
    stamp = f"{int(time.time())}-{os.getpid()}"
    paths = SabTaskPaths(
        benchmark_root=Path(args.benchmark_root),
        workdir=task_dir / stamp,
    )
    prepare_workdir(paths)
    spec = build_task_spec(row, args.instance_id, extra_rules=args.hint)
    client = client_from_config(args.config, args.arm)
    config = CodeActConfig(
        max_steps=args.max_steps,
        step_timeout_s=args.step_timeout,
        max_tokens=args.max_tokens,
        python_bin=args.python_bin,
    )
    run = run_codeact(paths, spec, client, config, agent_commit=git_commit())
    ev = run_eval(paths, eval_script, args.python_bin)

    out_dir = paths.workdir
    traj = run.trajectory
    assert traj is not None
    (out_dir / "trace.jsonl").write_text(traj.to_jsonl(), encoding="utf-8")
    summary = {
        "instance_id": args.instance_id,
        "arm": arm_dir,
        "hint": args.hint,
        "model_id": traj.meta.model_id,
        "snapshot": traj.meta.model_snapshot_or_revision,
        "agent_commit": traj.meta.agent_commit,
        "status": run.status,
        "eval_success": ev["success"],
        "eval_detail": ev["detail"],
        "eval_returncode": ev["returncode"],
        "eval_stdout_tail": ev["stdout_tail"][-500:],
        "eval_stderr_tail": ev["stderr_tail"][-500:],
        "final_answer": run.final_answer,
        "token_usage": run.token_usage,
        "wall_s": run.wall_s,
        "steps": run.steps,
        "usd_cost": "TBD (relay pricing not pinned)",
    }
    (out_dir / "result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in
                      ("instance_id", "status", "eval_success", "eval_detail",
                       "token_usage", "wall_s")}, ensure_ascii=False))
    return 0 if ev["success"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
