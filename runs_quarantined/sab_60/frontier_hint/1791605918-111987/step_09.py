#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

base = Path("benchmark/datasets/nvc")

for name in ["particularity.py","partneg.py"]:
    p = base/"scripts/nvc_prediction/rules"/name
    print(f"--- {name} ---")
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines, 1):
        print(f"{i:03d}: {line}")

ad = pd.read_csv(base/"accuracies_data_for_plot.csv")
print("\naccuracies_data_for_plot exact info")
print("shape", ad.shape)
print("columns", ad.columns.tolist())
print(ad.head(30).to_csv(index=False))
print("tail")
print(ad.tail(30).to_csv(index=False))
for col in ad.columns:
    print("COL", col, "dtype", ad[col].dtype, "nunique", ad[col].nunique())
    print(ad[col].dropna().unique()[:50])

# Check sequence/tasks all 64 and derive figure positions visually
rag = pd.read_csv(base/"Ragni2016.csv")
tasks = rag.drop_duplicates("sequence")[["sequence","task","choices"]].sort_values("sequence")
print("\nall tasks sequence/task first 64:")
for _, r in tasks.iterrows():
    print(int(r.sequence), r.task)