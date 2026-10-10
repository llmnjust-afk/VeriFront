#!/usr/bin/env python3
import os
from pathlib import Path

print("Working directory:", os.getcwd())
print("Top-level listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else "file")

print("\nSearching for bio_resting_5min_100hz.csv under current tree:")
matches = list(Path(".").rglob("bio_resting_5min_100hz.csv"))
for m in matches:
    print(" ", m.resolve())
print("Number of matches:", len(matches))

print("\nSearching one level up if needed:")
try:
    matches_up = list(Path("..").rglob("bio_resting_5min_100hz.csv"))
    for m in matches_up[:20]:
        print(" ", m.resolve())
    print("Number of matches up:", len(matches_up))
except Exception as e:
    print("Search up failed:", repr(e))