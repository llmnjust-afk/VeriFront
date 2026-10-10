#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

base = Path("benchmark/datasets/nvc")
print("base exists", base.exists())

for path in [
    base/"Ragni2016.csv",
    base/"valid_syllogisms.csv",
    base/"accuracies_data_for_plot.csv",
    base/"ind_data_for_plot.csv",
]:
    print("\n==", path)
    df = pd.read_csv(path)
    print("shape", df.shape)
    print("cols", list(df.columns))
    print(df.head(10).to_string(index=False))
    if "response" in df.columns:
        print("response value counts head")
        print(df["response"].value_counts().head(15).to_string())

print("\nModel CSVs")
for f in sorted((base/"scripts/indiv_table/models").glob("*.csv")):
    df = pd.read_csv(f)
    print("\n==", f.name, "shape", df.shape, "cols", list(df.columns))
    print(df.to_string(index=False))

print("\nRule code")
for f in sorted((base/"scripts/nvc_prediction/rules").glob("*.py")):
    if f.name == "__init__.py":
        continue
    print("\n==", f.name)
    print(f.read_text(errors="replace"))

print("\nExisting pred_results in benchmark if any")
pr = base/"scripts/indiv_table/pred_results"
print("exists", pr.exists())
if pr.exists():
    for f in sorted(pr.glob("*")):
        print(f, f.stat().st_size)
        if f.suffix == ".csv":
            try:
                df = pd.read_csv(f)
                print("shape", df.shape, "cols", list(df.columns))
                print(df.head().to_string(index=False))
            except Exception as e:
                print("err", repr(e))