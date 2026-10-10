#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("Searching nearby for existing polynomial_fit_pred.csv or scripts mentioning polynomial fit...")
base = Path("/data/lab/VeriFront/runs/sab_87/frontier")
matches = []
for p in base.rglob("*"):
    try:
        if p.is_file() and (p.name == "polynomial_fit_pred.csv" or p.suffix in [".py", ".txt", ".md", ".csv"]):
            if p.name == "polynomial_fit_pred.csv":
                matches.append(p)
            elif p.stat().st_size < 200000:
                txt = p.read_text(errors="ignore")
                if "polynomial_fit_pred" in txt or "polyfit" in txt or "A1B_north_america" in txt:
                    matches.append(p)
    except Exception:
        pass

for p in matches[:50]:
    print("\nMATCH:", p, "size", p.stat().st_size)
    try:
        if p.suffix == ".csv":
            print(pd.read_csv(p).head().to_string())
            print("columns:", list(pd.read_csv(p, nrows=0).columns))
        else:
            txt = p.read_text(errors="ignore")
            print(txt[:2000])
    except Exception as e:
        print("Could not display:", type(e).__name__, e)
print("Total matches:", len(matches))