#!/usr/bin/env python3
import os
import glob
import pandas as pd

print("Working directory:", os.getcwd())
print("Top-level entries:", sorted(os.listdir("."))[:100])
print("Searching for expected files under current tree (limited)...")
patterns = [
    "**/Ragni2016.csv",
    "**/valid_syllogisms.csv",
    "**/PSYCOP.csv",
    "**/negativity.py",
]
for pat in patterns:
    matches = glob.glob(pat, recursive=True)
    print(pat, "=>", matches[:20], "count", len(matches))

print("\nDirectory tree to depth 4:")
def walk_limited(path=".", max_depth=4):
    base_depth = path.rstrip(os.sep).count(os.sep)
    for root, dirs, files in os.walk(path):
        depth = root.count(os.sep) - base_depth
        if depth > max_depth:
            dirs[:] = []
            continue
        indent = "  " * depth
        print(f"{indent}{os.path.basename(root) or root}/")
        for f in sorted(files)[:30]:
            print(f"{indent}  {f} ({os.path.getsize(os.path.join(root,f))} bytes)")
        if len(files) > 30:
            print(f"{indent}  ... {len(files)-30} more files")
walk_limited(".", 4)

# If data is one level above or in common mounted paths, report.
for candidate in ["../nvc", "../../nvc", "/data/lab/VeriFront/nvc", "/data/lab/nvc", "/mnt/data/nvc"]:
    print(candidate, "exists?", os.path.exists(candidate))
    if os.path.exists(candidate):
        print(" entries:", os.listdir(candidate)[:20])