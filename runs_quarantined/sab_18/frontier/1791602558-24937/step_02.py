#!/usr/bin/env python3
import os
import glob

print("CWD:", os.getcwd())
print("Top-level entries:")
for p in sorted(os.listdir("."))[:100]:
    print(" ", p)

print("\nSearching for train/test csv files under cwd and nearby...")
patterns = [
    "**/train.csv", "**/test.csv", "**/*dili*/*.csv", "../**/train.csv", "../**/test.csv",
    "/data/lab/VeriFront/**/*.csv"
]
seen = set()
for pat in patterns:
    for p in glob.glob(pat, recursive=True):
        if p not in seen:
            seen.add(p)
            try:
                size = os.path.getsize(p)
            except OSError:
                size = -1
            print(p, size)
            if len(seen) > 200:
                print("Stopping search after 200 matches")
                raise SystemExit
print("Total csv-like matches:", len(seen))