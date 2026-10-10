#!/usr/bin/env python3
from pathlib import Path
import os

print("Working directory:", os.getcwd())
for root in [Path("benchmark"), Path("pred_results")]:
    print(f"\nListing {root}:")
    if root.exists():
        for p in sorted(root.rglob("*")):
            rel = p.relative_to(Path("."))
            print(" ", rel, "dir" if p.is_dir() else f"file ({p.stat().st_size} bytes)")
    else:
        print(" does not exist")

print("\nBroader search for CSV files under /data/lab/VeriFront (limited):")
base = Path("/data/lab/VeriFront")
count = 0
try:
    for p in base.rglob("*.csv"):
        print(" ", p)
        count += 1
        if count >= 100:
            print(" ... stopping at 100")
            break
except Exception as e:
    print("Error:", repr(e))
print("CSV count printed:", count)