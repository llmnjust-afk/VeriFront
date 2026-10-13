"""Generic artifact validators for feedback-intervention runs (plan §5.5).

A validator inspects the workdir AFTER the takeover step's execution and
returns a machine-checkable report. Reports may reference ONLY information
legally available at execution time (input data, produced artifacts,
runtime errors). Gold labels / reference answers / final-answer statistics
are NEVER read -- the module does not even import them.

v0 scope: existence, non-emptiness and CSV sanity of ``pred_results/``.
Used as (a) extra context in structured feedback, (b) no-op elsewhere.
The retry TRIGGER is execution status only -- identical across arms, so the
validator never changes WHEN a retry happens, only WHAT the retry sees.
"""
from __future__ import annotations

import csv
import os
from typing import Any, Dict


def run_report(workdir: str) -> Dict[str, Any]:
    """Return {"ok": bool, "issues": [...], "pred_results": [...]} JSON-safe."""
    rep: Dict[str, Any] = {"ok": True, "issues": [], "pred_results": []}
    pr = os.path.join(workdir, "pred_results")
    if not os.path.isdir(pr):
        rep["ok"] = False
        rep["issues"].append("pred_results/ directory missing (no artifacts produced yet)")
        return rep
    files: list = []
    for name in sorted(os.listdir(pr)):
        p = os.path.join(pr, name)
        if not os.path.isfile(p):
            continue
        st = os.stat(p)
        f: Dict[str, Any] = {"name": name, "bytes": st.st_size}
        if st.st_size == 0:
            f["empty_file"] = True
            rep["issues"].append(f"{name}: empty file (0 bytes)")
        elif name.endswith(".csv"):
            try:
                with open(p, newline="", encoding="utf-8", errors="replace") as fh:
                    rows = list(csv.reader(fh))
                header = rows[0] if rows else []
                ncols = len(header)
                nrows = max(0, len(rows) - 1)
                empty_cols = []
                for j in range(ncols):
                    if all(len(r) <= j or r[j].strip() == "" for r in rows[1:]):
                        empty_cols.append(header[j] if j < len(header) else f"col{j}")
                f.update({"rows": nrows, "cols": ncols,
                          "empty_cols": empty_cols[:10]})
                if nrows == 0:
                    rep["issues"].append(f"{name}: 0 data rows")
                if ncols == 0:
                    rep["issues"].append(f"{name}: no header row")
                if empty_cols:
                    rep["issues"].append(
                        f"{name}: entirely empty columns {empty_cols[:5]}")
            except Exception as e:  # unreadable csv
                f["csv_error"] = str(e)
                rep["issues"].append(f"{name}: unreadable csv ({e})")
        files.append(f)
    rep["pred_results"] = files
    if not files:
        rep["ok"] = False
        rep["issues"].append("pred_results/ exists but contains no files")
    elif rep["issues"]:
        rep["ok"] = False
    return rep
