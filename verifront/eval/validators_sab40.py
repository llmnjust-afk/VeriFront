"""t40 validator v2: step-aware artifact expectations (feedback-intervention sec5.5v2).

v1 (generic CSV sanity) is kept via the generic module. v2 adds EXPECTED
artifacts per takeover step, derived from the PARENT trajectory's produced
files (file NAMES only -- content/labels are never read, no gold leakage).

Expected after t40 step 4 (parent 305791):
  - at least one non-empty pred_results/MD_*_RF.csv with >0 data rows
  - pred_results/RF_training_summary.json exists, non-empty, parses as JSON
"""
from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict

from verifront.eval.validators_generic import run_report as generic_report

EXPECTED: Dict[int, Dict[str, Any]] = {
    4: {"md_csv_glob": "pred_results/MD_*_RF.csv",
        "summary_json": "pred_results/RF_training_summary.json"},
}


def run_report(workdir: str, step_no: int = None) -> Dict[str, Any]:
    rep = generic_report(workdir)
    exp = EXPECTED.get(step_no) if step_no is not None else None
    rep["expected_checked"] = []
    if not exp:
        return rep
    rep["expected_checked"] = sorted(exp.keys())
    md = sorted(glob.glob(os.path.join(workdir, exp["md_csv_glob"])))
    if not md:
        rep["issues"].append(f"no file matches {exp['md_csv_glob']} after step {step_no}")
        rep["ok"] = False
    else:
        for p in md:
            try:
                with open(p, newline="", encoding="utf-8", errors="replace") as fh:
                    rows = sum(1 for _ in fh) - 1
                if rows <= 0:
                    rep["issues"].append(f"{os.path.basename(p)}: 0 data rows")
                    rep["ok"] = False
            except Exception as e:
                rep["issues"].append(f"{os.path.basename(p)}: unreadable ({e})")
                rep["ok"] = False
    sp = os.path.join(workdir, exp["summary_json"])
    if not os.path.exists(sp):
        rep["issues"].append(f"expected artifact missing: {exp['summary_json']}")
        rep["ok"] = False
    elif os.path.getsize(sp) == 0:
        rep["issues"].append(f"expected artifact empty: {exp['summary_json']}")
        rep["ok"] = False
    else:
        try:
            json.load(open(sp, encoding="utf-8"))
        except Exception as e:
            rep["issues"].append(f"{os.path.basename(sp)}: not valid JSON ({e})")
            rep["ok"] = False
    return rep
