#!/usr/bin/env python3
"""Aggregate CF expansion results per replacement point."""
import argparse, glob, json, collections
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default="runs")
    ap.add_argument("--points", default="reports/annotation/cf_points.json")
    a = ap.parse_args()

    pts = {(p["task_id"], p["step_no"]): p
           for p in json.loads(Path(a.points).read_text())["points"]}
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    extras = collections.Counter()
    n_runs = 0
    for f in glob.glob(str(Path(a.runs_root) / "sab_*" / "cf_*" / "**" / "result.json"),
                       recursive=True):
        r = json.loads(Path(f).read_text()); m = r["cf_meta"]
        k = (str(r["instance_id"]), m["edit_step"])
        n_runs += 1
        if k not in pts:
            extras[(k, m["arm"], m["edit_model"] or "-")] += 1; continue
        arm = ("resample" if m["arm"] == "cf_frontier_resample"
               else ("mini" if "mini" in (m["edit_model"] or "") else "ds"))
        agg[k][arm].append(r["eval_success"])

    hdr = f"{'task':<5}{'step':<6}{'role':<5}{'outcome':<9}{'resample':<10}{'mini':<8}{'deepseek':<9}{'point_dSR':<10}"
    print(hdr)
    tot = {"resample": [0, 0], "mini": [0, 0], "ds": [0, 0]}
    interesting = []
    for (task, step) in sorted(agg, key=lambda x: (int(x[0]), x[1])):
        p = pts[(task, step)]
        a = agg[(task, step)]
        fmt = lambda v: f"{sum(v)}/{len(v)}"
        sr = {arm: (sum(v) / len(v) if v else None) for arm, v in a.items()}
        for arm in tot:
            if a.get(arm):
                tot[arm][0] += sum(a[arm]); tot[arm][1] += len(a[arm])
        # point-level delta: resample mean vs worst replace arm mean
        dsr = None
        if sr.get("resample") is not None and (sr.get("mini") or sr.get("ds")):
            worst = min(v for v in (sr.get("mini"), sr.get("ds")) if v is not None)
            dsr = sr["resample"] - worst
        if dsr:
            interesting.append(((task, step), dsr))
        print(f"{task:<5}{step:<6}{p['role'][:4]:<5}{p['run_outcome'][:8]:<9}"
              f"{fmt(a.get('resample', [])):<10}{fmt(a.get('mini', [])):<8}"
              f"{fmt(a.get('ds', [])):<9}{f'{dsr:+.2f}' if dsr is not None else '-':<10}")
    print(f"\ntotals: resample {tot['resample'][0]}/{tot['resample'][1]}"
          f" | mini {tot['mini'][0]}/{tot['mini'][1]} | ds {tot['ds'][0]}/{tot['ds'][1]}"
          f" | total runs incl. pilot: {n_runs}")
    if extras:
        print("non-plan runs:", dict(extras))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
