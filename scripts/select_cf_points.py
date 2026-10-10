#!/usr/bin/env python3
"""Select counterfactual replacement points from the adjudicated gold labels.

Joins annotator_gold.jsonl with annotation_sample.jsonl (run provenance via
stamp), verifies each parent run exists on disk and that its recorded outcome
matches, then emits a deterministic point list with arm/repeat plan.

Neutral sampling rule (deterministic): for each (task_id, run_outcome) group,
take the first neutral point by sample_idx; skip groups beyond one per outcome.
"""
import argparse
import json
import collections
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default="runs")
    ap.add_argument("--ann-dir", default="reports/annotation")
    ap.add_argument("--out", default="reports/annotation/cf_points.json")
    a = ap.parse_args()

    sample = {}
    for line in (Path(a.ann_dir) / "annotation_sample.jsonl").open():
        r = json.loads(line)
        sample[r["sample_idx"]] = r

    points, skipped = [], []
    per_group = collections.Counter()
    for line in (Path(a.ann_dir) / "annotator_gold.jsonl").open():
        g = json.loads(line)
        s = sample.get(g["i"])
        if s is None:
            skipped.append((g["i"], "no_sample")); continue
        for k in ("task_id", "step_idx", "run_outcome", "stratum"):
            if str(s[k]) != str(g[k]):
                skipped.append((g["i"], f"mismatch {k}")); break
        else:
            role = g["role_in_outcome"]
            if role == "neutral":
                key = (g["task_id"], g["run_outcome"])
                if per_group[key] >= 1:
                    skipped.append((g["i"], "neutral_quota")); continue
                per_group[key] += 1
            run_dir = Path(a.runs_root) / f"sab_{g['task_id']}" / "frontier" / s["stamp"]
            step_file = run_dir / f"{g['step_idx']}.py"
            ok = run_dir.is_dir() and (run_dir / "trace.jsonl").is_file() and step_file.is_file()
            points.append({
                "sample_idx": g["i"], "task_id": g["task_id"],
                "step_idx": g["step_idx"], "step_no": int(g["step_idx"].split("_")[1]),
                "role": role, "step_type": g["step_type"],
                "run_outcome": g["run_outcome"], "stratum": g["stratum"],
                "parent_stamp": s["stamp"], "parent_run": str(run_dir),
                "ready": ok,
            })

    n_ready = sum(p["ready"] for p in points)
    role_c = collections.Counter(p["role"] for p in points)
    summary = {
        "n_points": len(points), "n_ready": n_ready, "roles": dict(role_c),
        "planned_runs": n_ready * 4,
        "by_task": {t: sum(1 for p in points if p["task_id"] == t)
                    for t in sorted({p["task_id"] for p in points}, key=int)},
    }
    Path(a.out).write_text(json.dumps(
        {"summary": summary, "points": points, "skipped": skipped},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    for sk in skipped[:10]:
        print("SKIP:", sk)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
