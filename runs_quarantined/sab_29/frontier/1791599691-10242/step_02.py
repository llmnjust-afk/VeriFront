#!/usr/bin/env python3
import os
import glob
import json
import numpy as np
import pandas as pd

print("CWD:", os.getcwd())
print("Top-level listing:")
for p in sorted(os.listdir(".")):
    print(" ", repr(p), "dir" if os.path.isdir(p) else "file")

print("\nSearching for CSV files under current directory (depth unrestricted):")
csvs = sorted(glob.glob("**/*.csv", recursive=True))
for p in csvs[:200]:
    print(" ", p)
print("Total CSVs:", len(csvs))

# Also inspect nearby common roots if accessible
for root in ["..", "../..", "/data/lab/VeriFront", "/data/lab/VeriFront/runs"]:
    try:
        matches = glob.glob(os.path.join(root, "**", "bio_eventrelated_100hz.csv"), recursive=True)
        print(f"\nMatches under {root}: {len(matches)}")
        for m in matches[:20]:
            print(" ", m)
    except Exception as e:
        print(f"Search failed under {root}:", repr(e))

# If found, create a pointer file for later
matches = []
for root in [".", "..", "../..", "/data/lab/VeriFront"]:
    try:
        matches.extend(glob.glob(os.path.join(root, "**", "bio_eventrelated_100hz.csv"), recursive=True))
    except Exception:
        pass
matches = sorted(set(matches))
if matches:
    chosen = matches[0]
    print("\nChosen dataset path:", chosen)
    with open("dataset_path.txt", "w") as f:
        f.write(chosen)
    df = pd.read_csv(chosen)
    print("Loaded shape:", df.shape)
    print("Columns:", list(df.columns))
    print(df.head().to_string())
else:
    print("\nNo dataset found yet.")