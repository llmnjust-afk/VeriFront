"""Aggregate all SAB frontier runs into a summary table + cost rollup.

  python scripts/aggregate_runs.py [--runs runs/] [--out reports/pilot/]

Reads every runs/sab_<id>/frontier/<stamp>/result.json, deduplicates to the
LATEST run per (task, arm), and prints a markdown table with CA/USD cost
(gpt-5.5 default-group ladder, 0-272K tier). Also writes results_p1.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

IN_CA = 35.0 / 1e6   # CA per token, 0-272K ladder
OUT_CA = 210.0 / 1e6
CA_PER_USD = 7.15

SNAPSHOT = "gpt-5.5-2026-04-23"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default="reports/pilot")
    args = ap.parse_args()

    root = Path(args.runs)
    latest = {}
    for res in sorted(root.glob("sab_*/*/*/result.json")):
        r = json.loads(res.read_text(encoding="utf-8"))
        key = (r["instance_id"], r["arm"], res.parent.name)
        latest.setdefault((r["instance_id"], r["arm"]), []).append((res.parent.name, r))

    rows = []
    for (iid, arm), entries in sorted(latest.items(), key=lambda kv: kv[0][0]):
        for stamp, r in entries:
            tok = r.get("token_usage", {})
            p, c = tok.get("prompt", 0), tok.get("completion", 0)
            cost_ca = p * IN_CA + c * OUT_CA
            rows.append({
                "instance_id": iid, "arm": arm, "stamp": stamp,
                "status": r.get("status"), "eval_success": r.get("eval_success"),
                "eval_detail": r.get("eval_detail"),
                "prompt_tokens": p, "completion_tokens": c,
                "cost_CA": round(cost_ca, 4), "cost_USD": round(cost_ca / CA_PER_USD, 4),
                "wall_s": r.get("wall_s"),
                "snapshot": r.get("snapshot"),
            })

    rows.sort(key=lambda x: (x["instance_id"], x["stamp"]))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "results_p1.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    total_ca = sum(r["cost_CA"] for r in rows)
    total_usd = total_ca / CA_PER_USD
    succ = sum(1 for r in rows if r["eval_success"] == 1)
    print(f"| task | status | eval | tokens(p/c) | cost CA | wall s |")
    print(f"|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['instance_id']} ({r['stamp'][-6:]}) | {r['status']} | "
              f"{r['eval_success']} {r['eval_detail']} | {r['prompt_tokens']}/{r['completion_tokens']} | "
              f"{r['cost_CA']:.2f} | {r['wall_s']} |")
    print(f"\nruns={len(rows)} success={succ} total_cost={total_ca:.2f} CA = {total_usd:.2f} USD")
    print(f"csv -> {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
