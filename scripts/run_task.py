"""Run one task with an arm (frontier/local) via CodeAct-lite and persist the
trace. Usage:

  python scripts/run_task.py --config configs/models.yaml --arm frontier \
      --task-id demo --description-file task.md [--workdir runs/]

Writes runs/<task_id>/<arm>/<run_id>/trace.jsonl and result.json. The API key
never appears in any artifact; token_usage is recorded, USD cost stays TBD
until relay pricing is pinned.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verifront.agents.codeact import (  # noqa: E402
    CodeActAgent,
    CodeActConfig,
    TaskSpec,
    client_from_config,
)
from verifront.agents.base import load_models_config  # noqa: E402


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT),
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "configs/models.yaml"))
    ap.add_argument("--arm", default="frontier", help="frontier | local:<name>")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--description-file", required=True, help="path to task description text")
    ap.add_argument("--context-file", default=None, help="optional data dictionary text")
    ap.add_argument("--workdir", default=str(ROOT / "runs"))
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--step-timeout", type=float, default=300.0)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--python-bin", default=sys.executable)
    args = ap.parse_args()

    cfg = load_models_config(args.config)
    client = client_from_config(args.config, args.arm)
    description = Path(args.description_file).read_text(encoding="utf-8")
    extra = Path(args.context_file).read_text(encoding="utf-8") if args.context_file else ""
    task = TaskSpec(task_id=args.task_id, description=description, extra_context=extra)
    conf = CodeActConfig(
        max_steps=args.max_steps,
        step_timeout_s=args.step_timeout,
        max_tokens=args.max_tokens,
        python_bin=args.python_bin,
    )

    agent = CodeActAgent(client, conf, workdir=Path(args.workdir) / args.task_id / args.arm,
                         agent_commit=git_commit())
    result = agent.run(task)
    assert result.trajectory is not None

    out_dir = Path(args.workdir) / args.task_id / args.arm / f"{int(time.time())}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "trace.jsonl").write_text(result.trajectory.to_jsonl(), encoding="utf-8")
    summary = {
        "run_id": result.trajectory.meta.run_id,
        "task_id": args.task_id,
        "arm": args.arm,
        "model_id": result.trajectory.meta.model_id,
        "snapshot": result.trajectory.meta.model_snapshot_or_revision,
        "status": result.status,
        "final_answer": result.final_answer,
        "token_usage": result.token_usage,
        "wall_s": result.wall_s,
        "steps": result.steps,
        "usd_cost": "TBD (relay pricing not pinned)",
    }
    (out_dir / "result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in
                      ("run_id", "status", "token_usage", "wall_s")}, ensure_ascii=False))
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
