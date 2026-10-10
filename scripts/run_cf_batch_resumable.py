#!/usr/bin/env python3
"""Resumable executor for the CF expansion plan.

Reads cf_points.json, enumerates (point, arm, rep) jobs, skips jobs whose
result.json already exists, and runs the rest sequentially. On ChatError
(rate limit / 403), sleeps RETRY_WAIT seconds and retries the same job up
to MAX_RETRY times before giving up and moving on (job stays missing).
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ARMS = [("frontier_resample", None, None),
        ("local_replace", "gpt-5.4-mini-2026-03-17", "2026-03-17"),
        ("local_replace", "deepseek-v3.2", None)]
REPS = (1, 2)
RETRY_WAIT = 420.0
MAX_RETRY = 6


def result_exists(runs_root: Path, task: str, step: int, arm: str, model: str) -> bool:
    for f in (runs_root / f"sab_{task}" / f"cf_{arm}").glob("*/result.json"):
        try:
            r = json.loads(Path(f).read_text())
        except Exception:
            continue
        m = r.get("cf_meta") or {}
        if int(m.get("edit_step", -1)) != step:
            continue
        if (m.get("edit_model") or "") != (model or ""):
            continue
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default="reports/annotation/cf_points.json")
    ap.add_argument("--runs-root", default="runs")
    ap.add_argument("--only-batch", type=int, default=0,
                    help="1-based batch index over ready points (round-robin split of 4)")
    ap.add_argument("--n-batches", type=int, default=4)
    a = ap.parse_args()

    pts = [p for p in json.loads(Path(a.points).read_text())["points"] if p["ready"]]
    if a.only_batch:
        pts = [p for i, p in enumerate(pts) if i % a.n_batches == a.only_batch - 1]

    jobs = []
    for p in pts:
        for arm, model, snap in ARMS:
            for rep in REPS:
                jobs.append((p, arm, model, snap, rep))

    n_done = n_fail = 0
    abort = False
    for j, (p, arm, model, snap, rep) in enumerate(jobs, 1):
        if result_exists(Path(a.runs_root), p["task_id"], p["step_no"], arm, model or ""):
            n_done += 1
            continue
        cmd = [sys.executable, "scripts/run_cf_point.py",
               "--parent-run", p["parent_run"], "--at-step", str(p["step_no"]),
               "--arm", arm]
        if model:
            cmd += ["--edit-model", model]
            if snap:
                cmd += ["--edit-model-snapshot", snap]
        tag = f"t{p['task_id']}s{p['step_no']:02d}{p['role'][:2]}{'mini' if model and 'mini' in model else ('ds' if model else 'res')}"
        ok = False
        for attempt in range(1, MAX_RETRY + 1):
            print(f"[{j}/{len(jobs)}] {tag} {arm} {model or '-'} rep{rep} try{attempt} "
                  f"{time.strftime('%H:%M:%S')}", flush=True)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            last = (r.stdout or "").strip().splitlines()[-1] if (r.stdout or "").strip() else (r.stderr or "")[-200:]
            if r.returncode == 0 and '"status": "completed"' in (r.stdout or ""):
                print("   ->", last[:200], flush=True)
                ok = True
                break
            print(f"   FAIL rc={r.returncode}: {last[:220]}", flush=True)
            combined = (r.stderr or "") + (r.stdout or "")
            if "余额" in combined or "balance" in combined.lower():
                print("   account balance insufficient — aborting batch", flush=True)
                abort = True
                break
            if "403" in combined or "429" in combined:
                print(f"   rate-limited; sleeping {RETRY_WAIT:.0f}s", flush=True)
                time.sleep(RETRY_WAIT)
            else:
                time.sleep(15)
        n_done += ok
        n_fail += not ok
        if abort:
            break
    print(f"BATCH-SEGMENT DONE: done={n_done} missing_after_retries={n_fail}"
          + (" ABORTED_BALANCE" if abort else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
