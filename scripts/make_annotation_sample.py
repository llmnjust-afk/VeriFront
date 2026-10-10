"""Build the 60-step trial annotation set from frozen-config frontier runs.

  python scripts/make_annotation_sample.py [--n 60]

Walks runs/sab_<id>/frontier/*/trace.jsonl (latest stamp per (task, arm)),
extracts steps, applies heuristic pre-labels, stratifies sampling across
stable-pass / stable-fail / flaky tasks, writes
reports/annotation/annotation_sample.jsonl with blank human judgment fields.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
OUT = ROOT / "reports/annotation/annotation_sample.jsonl"

STABLE_PASS = {18, 37, 40, 45, 53, 58, 67, 85}
STABLE_FAIL = {34, 35, 44, 60, 87, 92}
FLAKY = {5, 29}

SIG = {
    "data_inspection": r"\.head\(|\.columns|listdir|glob\.|\.shape|print.*shape|glob.glob",
    "data_prep": r"read_csv|read_json|np\.load|MorganFingerprint|GetMorgan|\.fit_transform|resample|StandardScaler|to_numpy|concatenate",
    "method_design": r"RandomForest|GridSearch|KFold|SVC|class_weight|ecg_peaks|hrv|def main|Pipeline|param_grid|rules\.|nvc_rule|GroupKFold|StratifiedKFold",
    "compute_run": r"\.fit\(|grid\.fit|predict\(|to_csv\(.*pred_results|json\.dump.*pred_results",
    "eval_check": r"assert |print.*match|check|sanity|verify|unique\(|isna|equals",
    "fix_rerun": r"KeyError|Traceback|Error|fix|retry",
}
RE_SIG = {k: re.compile(v) for k, v in SIG.items()}


def classify(text: str, is_final: bool) -> str:
    if is_final:
        return "final_report"
    scores = {k: len(rx.findall(text)) for k, rx in RE_SIG.items()}
    if not any(scores.values()):
        return "data_inspection"
    return max(scores, key=lambda k: scores[k])


def load_steps():
    steps = []
    for tdir in sorted(RUNS.glob("sab_*/frontier/*")):
        trace = tdir / "trace.jsonl"
        res = tdir / "result.json"
        if not trace.is_file() or not res.is_file():
            continue
        m = re.match(r"sab_(\d+)", tdir.parent.parent.name)
        if not m:
            continue
        tid = int(m.group(1))
        events = [json.loads(l) for l in trace.open(encoding="utf-8")]
        run = json.loads(res.read_text(encoding="utf-8"))
        idx = 0
        for e in events:
            if e.get("event_type") != "agent_message":
                continue
            ctx = e.get("visible_agent_context", "") or ""
            is_final = "<final>" in ctx
            body = re.search(r"<(?:code|final)>(.*?)</(?:code|final)>", ctx, re.S)
            text = body.group(1) if body else ctx
            idx += 1
            steps.append({
                "trajectory_id": run.get("snapshot", "") + f"/{tdir.name}",
                "instance_id": tid,
                "run_status": run.get("status"),
                "eval_success": run.get("eval_success"),
                "step_idx": idx,
                "stratum": ("stable_pass" if tid in STABLE_PASS else
                            "stable_fail" if tid in STABLE_FAIL else "flaky"),
                "text": text[:4000],
                "pre_step_type": classify(text, is_final),
                "pre_is_final": is_final,
            })
    return steps


def sample(steps, n=60):
    rng = __import__("random").Random(42)
    picked = list(steps)  # full pool; quotas decide composition
    per_task = {}
    quota = {"method_design": 14, "fix_rerun": 8, "eval_check": 10, "data_prep": 10,
             "compute_run": 12, "data_inspection": 8, "final_report": 6}
    used = {k: 0 for k in quota}
    out = []
    prio = ["method_design", "fix_rerun", "eval_check", "data_prep",
            "compute_run", "data_inspection", "final_report"]
    rng.shuffle(picked)
    for p in prio:
        for s in [s for s in picked if s["pre_step_type"] == p]:
            if used[p] >= quota[p] or len(out) >= n:
                continue
            if per_task.get(s["instance_id"], 0) >= 5:
                continue
            per_task[s["instance_id"]] = per_task.get(s["instance_id"], 0) + 1
            used[p] += 1
            out.append(s)
    if len(out) < n:  # relax per-task cap before touching class quotas
        for s in picked:
            if len(out) >= n:
                break
            if s not in out:
                out.append(s)
    return sorted(out, key=lambda x: (x["instance_id"], x["trajectory_id"], x["step_idx"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    args = ap.parse_args()
    steps = load_steps()
    sel = sample(steps, args.n)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for s in sel:
            rec = {
                "trajectory_id": s["trajectory_id"],
                "instance_id": s["instance_id"],
                "run_status": s["run_status"],
                "eval_success": s["eval_success"],
                "step_idx": s["step_idx"],
                "stratum": s["stratum"],
                "step_text": s["text"],
                "machine_prelabel": s["pre_step_type"],
                "HUMAN_step_type": "",
                "HUMAN_role_in_outcome": "",
                "HUMAN_content_summary": "",
                "HUMAN_dependency": "",
                "HUMAN_anchor_flag": "",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {len(sel)} steps -> {OUT}")
    from collections import Counter
    print("by stratum:", dict(Counter(s["stratum"] for s in sel)))
    print("by prelabel:", dict(Counter(s["pre_step_type"] for s in sel)))


if __name__ == "__main__":
    main()
