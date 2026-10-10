#!/usr/bin/env python3
import os
import pandas as pd
from pathlib import Path

root = Path("nvc")
print("Working directory:", Path.cwd())
print("Exists nvc:", root.exists())

for path in [
    "nvc/Ragni2016.csv",
    "nvc/valid_syllogisms.csv",
    "nvc/accuracies_data_for_plot.csv",
    "nvc/ind_data_for_plot.csv",
]:
    p = Path(path)
    print("\n==", path, "exists", p.exists(), "size", p.stat().st_size if p.exists() else None)
    if p.exists():
        try:
            df = pd.read_csv(p)
            print("shape", df.shape)
            print("columns", list(df.columns))
            print(df.head(5).to_string(index=False))
        except Exception as e:
            print("read error", repr(e))

for sub in [
    "nvc/scripts/indiv_table/models",
    "nvc/scripts/prediction_errors/models",
    "nvc/scripts/indiv_table/rules",
    "nvc/scripts/prediction_errors/rules",
    "nvc/scripts/nvc_prediction/rules",
]:
    p = Path(sub)
    print("\nDIR", sub, "exists", p.exists())
    if p.exists():
        for f in sorted(p.iterdir()):
            print(" ", f.name, f.stat().st_size)

# Inspect model CSV schemas and rule Python headers.
for model_dir in ["nvc/scripts/indiv_table/models", "nvc/scripts/prediction_errors/models"]:
    p = Path(model_dir)
    if p.exists():
        print("\nMODEL DIR SAMPLE", model_dir)
        for f in sorted(p.glob("*.csv")):
            try:
                df = pd.read_csv(f)
                print(f.name, "shape", df.shape, "cols", list(df.columns))
                print(df.head(3).to_string(index=False))
            except Exception as e:
                print(f.name, "ERR", repr(e))
            break

for rule_dir in ["nvc/scripts/indiv_table/rules", "nvc/scripts/prediction_errors/rules", "nvc/scripts/nvc_prediction/rules"]:
    p = Path(rule_dir)
    if p.exists():
        print("\nRULE DIR SAMPLE", rule_dir)
        for f in sorted(p.glob("*.py")):
            if f.name == "__init__.py":
                continue
            print("FILE", f)
            txt = f.read_text(errors="replace").splitlines()
            for line in txt[:80]:
                print(line)
            break