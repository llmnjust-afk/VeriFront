#!/usr/bin/env python3
import os
from pathlib import Path

print("Working directory:", os.getcwd())
print("Top-level listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else "file")

print("\nSearching for ecg data files up to depth 5...")
patterns = ["ecg_data.pkl", "sampling_rate.txt", "ecg_processing_data"]
for pattern in patterns:
    print(f"\nMatches for {pattern}:")
    count = 0
    for p in Path(".").glob(f"**/{pattern}"):
        print(" ", p)
        count += 1
        if count > 50:
            print("  ... stopping after 50")
            break
    if count == 0:
        print("  none")

print("\nSearching parent /data/lab subtree shallowly for ecg_processing_data...")
base = Path("/data/lab")
count = 0
try:
    for p in base.glob("**/ecg_processing_data"):
        print(" ", p)
        count += 1
        if count >= 20:
            print("  ... stopping after 20")
            break
except Exception as e:
    print("Search error:", repr(e))
print("Done.")