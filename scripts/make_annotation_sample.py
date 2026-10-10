#!/usr/bin/env python3
"""Sample steps from sanitized run artifacts for the annotation reliability study.

Strata (third sandbox batch, frozen matrix 2026-10-10):
  stable_pass = {18,37,45,53,60,85,92}  stable_fail = {5,34,35,44,67,87}  flaky = {29,40,58}
Only frontier (frozen) runs are sampled; hint runs are excluded to keep the
trial corpus behaviorally homogeneous. Step bodies come from the run's
step_NN.py artifacts (trace records only the sha256).
"""
from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "runs"
OUT = REPO / "reports" / "annotation"

STABLE_PASS = {"18", "37", "45", "53", "60", "85", "92"}
STABLE_FAIL = {"5", "34", "35", "44", "67", "87"}
FLAKY = {"29", "40", "58"}
QUOTA = {"stable_pass": 34, "stable_fail": 20, "flaky": 6}
SEED = 20261010

def stratum(task: str) -> str | None:
    if task in STABLE_PASS: return "stable_pass"
    if task in STABLE_FAIL: return "stable_fail"
    if task in FLAKY: return "flaky"
    return None

def load_frozen_runs() -> list[dict]:
    recs = []
    for task_dir in sorted(RUNS.glob("sab_*"), key=lambda p: int(p.name.split("_")[1])):
        task = task_dir.name.split("_")[1]
        st = stratum(task)
        if st is None: continue
        for run_dir in sorted(task_dir.glob("frontier/1791*")):
            if int(run_dir.name.split("-")[0]) < 1791612600: continue
            result_file = run_dir / "result.json"
            if not result_file.is_file(): continue
            result = json.loads(result_file.read_text())
            outcome = "success" if result.get("eval_success") else "failure"
            for step_file in sorted(run_dir.glob("step_*.py")):
                code = step_file.read_text()
                if not code.strip(): continue
                recs.append({
                    "task_id": task, "stratum": st, "run_outcome": outcome,
                    "stamp": run_dir.name,
                    "step_idx": step_file.stem,
                    "code": code,
                    "obs_sha": "",
                })
    return recs

def main() -> None:
    recs = load_frozen_runs()
    print(f"corpus steps: {len(recs)}")
    pools: dict[str, list[dict]] = {"stable_pass": [], "stable_fail": [], "flaky": []}
    for r in recs:
        pools[r["stratum"]].append(r)
    rng = random.Random(SEED)
    sample = []
    for st, n in QUOTA.items():
        pool = pools[st]
        if len(pool) < n:
            print(f"WARN: {st} pool {len(pool)} < quota {n}")
        sample += rng.sample(pool, min(n, len(pool)))
    for i, r in enumerate(sample, 1):
        r["sample_idx"] = i
    rng.shuffle(sample)  # shuffle AFTER numbering; annotators see # in random order
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "annotation_sample.jsonl").open("w") as f:
        for r in sample:
            f.write(json.dumps(r) + "\n")
    print("sampled:", Counter(r["stratum"] for r in sample))
    digest = OUT / "trial_digest.txt"
    with digest.open("w") as f:
        for r in sample:
            head = re.sub(r"\s+", " ", r["code"])[:300]
            f.write(f"#{r['sample_idx']} task={r['task_id']} stratum={r['stratum']} outcome={r['run_outcome']} step={r['step_idx']}\n{head}\n\n")
    print("digest ->", digest)

if __name__ == "__main__":
    main()
