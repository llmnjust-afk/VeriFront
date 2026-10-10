#!/usr/bin/env python3
import os
import pandas as pd
from pathlib import Path

base = Path("nvc")
print("Working directory:", Path.cwd())
print("Exists nvc:", base.exists())

for p in [
    base/"ind_data_for_plot.csv",
    base/"valid_syllogisms.csv",
    base/"accuracies_data_for_plot.csv",
    base/"Ragni2016.csv",
]:
    print("\nFILE", p, "exists", p.exists(), "size", p.stat().st_size if p.exists() else None)
    if p.exists():
        try:
            df = pd.read_csv(p)
            print("shape:", df.shape)
            print("columns:", list(df.columns))
            print(df.head().to_string(index=False))
        except Exception as e:
            print("read error:", repr(e))

for sub in ["indiv_table", "prediction_errors"]:
    print("\n==", sub, "models ==")
    mdir = base/"scripts"/sub/"models"
    for p in sorted(mdir.glob("*.csv")):
        print("\nMODEL FILE", p.name, "size", p.stat().st_size)
        try:
            df = pd.read_csv(p)
            print("shape:", df.shape)
            print("columns:", list(df.columns))
            print(df.head(10).to_string(index=False))
        except Exception as e:
            print("read error:", repr(e))

print("\n== rules files snippets ==")
for sub in ["indiv_table", "prediction_errors", "nvc_prediction"]:
    rdir = base/"scripts"/sub/"rules"
    print("\nRULE DIR", rdir)
    for p in sorted(rdir.glob("*.py")):
        print(" ", p.name, "size", p.stat().st_size)
        txt = p.read_text(errors="replace").splitlines()
        print("   first lines:", " | ".join(txt[:5]))