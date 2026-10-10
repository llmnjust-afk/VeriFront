#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import os

base = Path("benchmark/datasets/nvc")
print("Files in nvc/scripts:")
for p in sorted((base/"scripts").rglob("*.py")):
    print("==", p.relative_to(base))
    txt = p.read_text(errors="replace").splitlines()
    print("\n".join(txt[:60]))
    print("---")

print("\nvalid_syllogisms full:")
print(pd.read_csv(base/"valid_syllogisms.csv").to_string(index=False))

print("\naccuracies_data_for_plot columns/sample:")
ad = pd.read_csv(base/"accuracies_data_for_plot.csv")
print(ad.shape, list(ad.columns))
print(ad.head(20).to_string(index=False))
print(ad.tail(20).to_string(index=False))

print("\nind_data_for_plot:")
print(pd.read_csv(base/"ind_data_for_plot.csv").to_string(index=False))

print("\nModel CSVs compact:")
for f in sorted((base/"scripts/indiv_table/models").glob("*.csv")):
    df = pd.read_csv(f)
    print("\n==", f.name, "shape", df.shape, "cols", list(df.columns))
    print(df.to_csv(index=False))

print("\nRule function signatures/logic concise:")
for f in sorted((base/"scripts/nvc_prediction/rules").glob("*.py")):
    if f.name == "__init__.py": continue
    lines = f.read_text(errors="replace").splitlines()
    print("\n==", f.name)
    for i,line in enumerate(lines,1):
        if i <= 80:
            print(f"{i:03d}: {line}")