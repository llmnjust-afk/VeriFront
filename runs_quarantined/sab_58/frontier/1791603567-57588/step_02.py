#!/usr/bin/env python3
import os
import glob
import pandas as pd

print("CWD:", os.getcwd())
print("Top-level entries:")
for name in sorted(os.listdir(".")):
    try:
        print(name, "dir" if os.path.isdir(name) else f"file {os.path.getsize(name)} bytes")
    except Exception as e:
        print(name, e)

print("\nSearching for relevant files up to depth 5...")
patterns = ["**/Ragni2016.csv", "**/ind_data_for_plot.csv", "**/PSYCOP.csv", "**/atmosphere.py", "**/valid_syllogisms.csv"]
for pat in patterns:
    matches = glob.glob(pat, recursive=True)
    print(pat, "->", matches[:20], "count", len(matches))

print("\nDirectory tree shallow:")
for root, dirs, files in os.walk("."):
    depth = root.count(os.sep)
    if depth > 4:
        dirs[:] = []
        continue
    print("  " * depth + os.path.basename(root or ".") + "/")
    for f in files[:10]:
        print("  " * depth + "  " + f)
    if len(files) > 10:
        print("  " * depth + f"  ... {len(files)-10} more")