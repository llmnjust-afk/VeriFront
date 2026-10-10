#!/usr/bin/env python3
from pathlib import Path
import os

print("cwd", Path.cwd())
print("Top-level entries:")
for p in sorted(Path(".").iterdir()):
    print(("DIR " if p.is_dir() else "FILE"), p, "size", (p.stat().st_size if p.is_file() else ""))

print("\nSearching for expected files/directories up to depth 5...")
names = {"Ragni2016.csv","ind_data_for_plot.csv","valid_syllogisms.csv","accuracies_data_for_plot.csv","PSYCOP.csv","Matching.csv"}
count=0
for root, dirs, files in os.walk("."):
    depth = Path(root).relative_to(".").parts
    if len(depth) > 5:
        dirs[:] = []
        continue
    for f in files:
        if f in names or "Ragni" in f or f.endswith(".csv"):
            path = Path(root)/f
            print(path, "size", path.stat().st_size)
            count += 1
            if count > 200:
                print("... stopping after 200")
                raise SystemExit
print("found count", count)

print("\nParent entries:")
parent = Path("..")
for p in sorted(parent.iterdir())[:100]:
    print(("DIR " if p.is_dir() else "FILE"), p)