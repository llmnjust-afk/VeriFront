#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("cwd", os.getcwd())

# targeted search in benchmark for nvc or known filenames, with pruning-ish manual walk
targets = {"Ragni2016.csv", "valid_syllogisms.csv", "accuracies_data_for_plot.csv", "PSYCOP.csv"}
hits = []
for p in Path("benchmark").rglob("*"):
    if p.name in targets or p.name == "nvc":
        hits.append(p)
        print("HIT", p, "DIR" if p.is_dir() else p.stat().st_size)
        if len(hits) > 100:
            break
print("total hits printed", len(hits))

# list likely nvc dirs
for p in hits:
    if p.is_dir() and p.name == "nvc":
        print("\nNVC tree under", p)
        for q in sorted(p.rglob("*")):
            if q.is_file():
                print(q, q.stat().st_size)
        break

# Inspect if any Ragni found
for p in hits:
    if p.name == "Ragni2016.csv":
        print("Reading", p)
        df = pd.read_csv(p)
        print(df.shape, list(df.columns))
        print(df.head().to_string(index=False))
        break