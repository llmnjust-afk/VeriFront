#!/usr/bin/env python3
"""Generate batch shell scripts for the CF point expansion.

Each point -> 6 runs: resample x2, mini-replace x2, deepseek-replace x2.
Points are round-robin split into N batches so each batch touches all roles.
"""
import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default="reports/annotation/cf_points.json")
    ap.add_argument("--batches", type=int, default=4)
    ap.add_argument("--out-prefix", default="/data/lab/cfB")
    a = ap.parse_args()

    data = json.loads(Path(a.points).read_text())
    pts = [p for p in data["points"] if p["ready"]]
    n = len(pts)
    groups = [[] for _ in range(a.batches)]
    for i, p in enumerate(pts):
        groups[i % a.batches].append(p)

    total = 0
    for bi, group in enumerate(groups, 1):
        lines = ["#!/bin/bash", "set -a", ". /data/lab/.verifront_env", "set +a",
                 "cd /data/lab/VeriFront", ""]
        for p in group:
            run = p["parent_run"]
            step = p["step_no"]
            pid = f"t{p['task_id']}s{step:02d}{p['role'][:2]}"
            for rep in (1, 2):
                lines.append(f"echo '===== {pid} resample r{rep} '$(date -Is)")
                lines.append(f"python3 scripts/run_cf_point.py --parent-run {run} --at-step {step} "
                             f"--arm frontier_resample 2>&1 | tail -1")
                lines.append(f"echo '===== {pid} mini r{rep} '$(date -Is)")
                lines.append(f"python3 scripts/run_cf_point.py --parent-run {run} --at-step {step} "
                             f"--arm local_replace --edit-model gpt-5.4-mini-2026-03-17 "
                             f"--edit-model-snapshot 2026-03-17 2>&1 | tail -1")
                lines.append(f"echo '===== {pid} deepseek r{rep} '$(date -Is)")
                lines.append(f"python3 scripts/run_cf_point.py --parent-run {run} --at-step {step} "
                             f"--arm local_replace --edit-model deepseek-v3.2 2>&1 | tail -1")
                total += 3
        lines.append(f"echo CF-BATCH{bi}-DONE")
        out = Path(f"{a.out_prefix}{bi}.sh")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"batch {bi}: {len(group)} points, {len(group)*6} runs -> {out}")
    print(f"TOTAL runs: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
