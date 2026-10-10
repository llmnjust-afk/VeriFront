#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("CWD:", Path.cwd())
print("Top-level listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else "file")

print("\nSearching for expected files/directories up to depth 5...")
names = {
    "Ragni2016.csv", "valid_syllogisms.csv", "accuracies_data_for_plot.csv",
    "ind_data_for_plot.csv", "PSYCOP.csv", "Matching.csv", "VerbalModels.csv",
    "MMT.csv", "Conversion.csv", "PHM.csv", "Atmosphere.csv"
}
found = []
for p in Path(".").rglob("*"):
    if len(p.parts) <= 7 and (p.name in names or p.name == "nvc"):
        found.append(p)
for p in sorted(found):
    print(p)

# Also search one level above if accessible
parent = Path("..")
print("\nParent listing:")
try:
    for p in sorted(parent.iterdir())[:100]:
        print(" ", p)
except Exception as e:
    print("parent list error", repr(e))

print("\nSearching /data/lab/VeriFront/runs/sab_60/frontier for nvc-ish items limited...")
base = Path("/data/lab/VeriFront/runs/sab_60/frontier")
try:
    count = 0
    for p in base.rglob("Ragni2016.csv"):
        print("Ragni found:", p)
        count += 1
        if count >= 20:
            break
    print("Ragni search count printed:", count)
except Exception as e:
    print("search error:", repr(e))