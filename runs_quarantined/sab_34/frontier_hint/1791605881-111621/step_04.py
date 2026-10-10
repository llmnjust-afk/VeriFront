#!/usr/bin/env python3
from pathlib import Path
import os

print("Working directory:", os.getcwd())

search_roots = [Path("."), Path("/data/lab/VeriFront")]
targets = ["bio_resting_5min_100hz.csv", "bio_eventrelated_100hz.csv", "ecg_1000hz.csv", "eog_100hz.csv"]
for root in search_roots:
    print(f"\nTargeted os.walk search under {root}:")
    found = []
    visited = 0
    for dirpath, dirnames, filenames in os.walk(root):
        visited += 1
        # prune common massive/irrelevant dirs only after checking current dir
        for t in targets:
            if t in filenames:
                found.append(Path(dirpath) / t)
                print(" FOUND", Path(dirpath) / t)
        if visited % 10000 == 0:
            print(" visited dirs:", visited, "current:", dirpath)
        if visited > 200000:
            print(" stopping after 200000 dirs")
            break
    print("Visited dirs:", visited, "Found:", len(found))

print("\nLooking for directories named biosignals or containing bio in name under benchmark/datasets:")
base = Path("benchmark/datasets")
matches = []
if base.exists():
    for p in base.rglob("*"):
        if p.is_dir() and "bio" in p.name.lower():
            matches.append(p)
            print(" ", p)
            if len(matches) >= 50:
                print(" stopping at 50")
                break
print("Bio-like dirs found:", len(matches))