#!/usr/bin/env python3
from pathlib import Path
import os, pandas as pd

print("Searching specifically for nvc/Ragni2016.csv and related paths under benchmark...")
matches = []
for root, dirs, files in os.walk("benchmark"):
    # skip very large irrelevant hidden/cache dirs if any
    if "Ragni2016.csv" in files or Path(root).name == "nvc" or "ind_data_for_plot.csv" in files:
        matches.append(Path(root))
        print("MATCH ROOT:", root)
        print("  dirs:", dirs[:20])
        print("  files:", files[:30])
print("num match roots", len(matches))

print("\nSearching filenames containing Ragni or nvc under benchmark...")
count=0
for root, dirs, files in os.walk("benchmark"):
    for f in files:
        if "Ragni" in f or "nvc" in f.lower() or f in ["valid_syllogisms.csv","accuracies_data_for_plot.csv"]:
            p=Path(root)/f
            print(p, p.stat().st_size)
            count+=1
print("count", count)

# Try known possible base
candidates = [
    Path("benchmark/datasets/nvc"),
    Path("benchmark/nvc"),
    Path("benchmark/datasets/NVC"),
]
for base in candidates:
    print("\nCandidate", base, "exists", base.exists())
    if base.exists():
        for p in base.rglob("*"):
            if p.is_file():
                print(p, p.stat().st_size)
        for p in [base/"ind_data_for_plot.csv", base/"Ragni2016.csv"]:
            if p.exists():
                df=pd.read_csv(p)
                print("\nPreview", p, df.shape, list(df.columns))
                print(df.head().to_string(index=False))