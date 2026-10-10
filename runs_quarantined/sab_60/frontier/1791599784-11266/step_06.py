#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
root=Path("benchmark/datasets/nvc")

def show(path, n=5):
    df=pd.read_csv(path)
    print("\n==", path, "shape", df.shape)
    print("cols:", list(df.columns))
    print(df.head(n).to_string(index=False))
    for c in df.columns:
        if df[c].dtype=='object':
            vals=df[c].dropna().unique()
            print(c, "unique n", len(vals), "sample", vals[:20])
        else:
            print(c, "min/max", df[c].min(), df[c].max(), "unique", df[c].nunique())
    return df

acc=show(root/"accuracies_data_for_plot.csv", 8)
ind=show(root/"ind_data_for_plot.csv", 8)
valid=show(root/"valid_syllogisms.csv", 20)

print("\nModel files concise:")
for f in sorted((root/"scripts/indiv_table/models").glob("*.csv")):
    df=pd.read_csv(f)
    print("\n", f.name, df.shape, list(df.columns))
    print(df.to_string(index=False))

print("\nRule file names and function defs:")
for f in sorted((root/"scripts/prediction_errors/rules").glob("*.py")):
    txt=f.read_text().splitlines()
    print("\n", f.name)
    for line in txt:
        if line.strip().startswith("def ") or line.strip().startswith("class ") or "return" in line:
            print(line)