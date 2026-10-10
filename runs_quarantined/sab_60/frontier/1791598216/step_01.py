#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd

root = Path("nvc")
print("Working directory:", Path.cwd())
print("Exists nvc:", root.exists())

# Print relevant file inventory and shapes/heads to understand data formats
paths = [
    root / "Ragni2016.csv",
    root / "valid_syllogisms.csv",
    root / "accuracies_data_for_plot.csv",
    root / "ind_data_for_plot.csv",
]
for p in paths:
    print("\nFILE", p, "exists=", p.exists())
    if p.exists():
        try:
            df = pd.read_csv(p)
            print("shape:", df.shape)
            print("columns:", list(df.columns))
            print(df.head(5).to_string(index=False))
        except Exception as e:
            print("Could not read:", repr(e))

for sub in [
    root / "scripts" / "indiv_table" / "models",
    root / "scripts" / "prediction_errors" / "models",
]:
    print("\nDIR", sub, "exists=", sub.exists())
    if sub.exists():
        for f in sorted(sub.glob("*.csv")):
            try:
                df = pd.read_csv(f)
                print(f.name, "shape", df.shape, "cols", list(df.columns))
                print(df.head(3).to_string(index=False))
            except Exception as e:
                print(f.name, "ERR", repr(e))

for sub in [
    root / "scripts" / "indiv_table" / "rules",
    root / "scripts" / "prediction_errors" / "rules",
    root / "scripts" / "nvc_prediction" / "rules",
]:
    print("\nRULE DIR", sub, "exists=", sub.exists())
    if sub.exists():
        for f in sorted(sub.glob("*.py")):
            print("----", f)
            txt = f.read_text()
            print("\n".join(txt.splitlines()[:80]))