#!/usr/bin/env python3
"""
Inspect available files to locate the questionnaire dataset or benchmark-provided
artifacts. This turn only prints directory information needed for the next step.
"""
from pathlib import Path
import os

print("CWD:", Path.cwd())

def list_tree(root, max_depth=4, max_entries=300):
    root = Path(root)
    print(f"\nTREE for {root} (exists={root.exists()}):")
    if not root.exists():
        return
    count = 0
    root_depth = len(root.resolve().parts)
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        depth = len(d.resolve().parts) - root_depth
        if depth > max_depth:
            dirnames[:] = []
            continue
        indent = "  " * depth
        print(f"{indent}{d.name}/")
        count += 1
        if count >= max_entries:
            print("... entry limit reached")
            return
        for fn in sorted(filenames):
            print(f"{indent}  {fn}")
            count += 1
            if count >= max_entries:
                print("... entry limit reached")
                return

for root in [".", "benchmark", "/data/lab/VeriFront/runs/sab_45/frontier/1791601836-18853/benchmark", "/data/lab/VeriFront/runs/sab_45", "/data/lab/VeriFront/runs"]:
    list_tree(root, max_depth=5, max_entries=500)

print("\nSearching selected locations for any .pkl/.csv/.parquet files:")
for root in [Path("."), Path("benchmark"), Path("/data/lab/VeriFront/runs/sab_45"), Path("/data/lab/VeriFront/runs")]:
    if not root.exists():
        continue
    try:
        matches = []
        for pat in ["*.pkl", "*.pickle", "*.csv", "*.parquet", "*.tsv", "*.json"]:
            matches.extend(root.rglob(pat))
        print(f"\n{root}: {len(matches)} matches")
        for m in sorted(matches)[:100]:
            print(" ", m)
    except Exception as e:
        print(f"Error searching {root}: {e}")