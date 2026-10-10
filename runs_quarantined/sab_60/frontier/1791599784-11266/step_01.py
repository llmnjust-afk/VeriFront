#!/usr/bin/env python3
import os
import pandas as pd
from pathlib import Path

print("Working directory:", os.getcwd())
root = Path("nvc")
print("nvc exists:", root.exists())
for p in sorted(root.rglob("*")):
    if p.is_file():
        print(p, "size", p.stat().st_size)

# Inspect key CSVs: columns, shapes, first rows
for fname in [
    "nvc/Ragni2016.csv",
    "nvc/valid_syllogisms.csv",
    "nvc/ind_data_for_plot.csv",
    "nvc/accuracies_data_for_plot.csv",
]:
    path = Path(fname)
    if path.exists():
        print("\n===", fname, "===")
        try:
            df = pd.read_csv(path)
            print("shape:", df.shape)
            print("columns:", list(df.columns))
            print(df.head(10).to_string(index=False))
        except Exception as e:
            print("ERROR reading", fname, repr(e))

# Inspect model CSVs in both locations
for sub in ["indiv_table/models", "prediction_errors/models"]:
    d = root / "scripts" / sub
    print("\n=== listing", d, "===")
    if d.exists():
        for f in sorted(d.glob("*.csv")):
            print("\n---", f, "---")
            try:
                df = pd.read_csv(f)
                print("shape:", df.shape)
                print("columns:", list(df.columns))
                print(df.head(8).to_string(index=False))
            except Exception as e:
                print("ERROR:", repr(e))

# Inspect rule python files text headers
for sub in ["indiv_table/rules", "prediction_errors/rules", "nvc_prediction/rules"]:
    d = root / "scripts" / sub
    print("\n=== rule files", d, "===")
    if d.exists():
        for f in sorted(d.glob("*.py")):
            print("\n---", f, "---")
            try:
                lines = f.read_text().splitlines()
                print("\n".join(lines[:80]))
            except Exception as e:
                print("ERROR:", repr(e))