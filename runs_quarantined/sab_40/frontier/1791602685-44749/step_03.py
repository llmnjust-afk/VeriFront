#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("CWD:", Path.cwd())
for root in [Path("."), Path("benchmark"), Path("pred_results")]:
    print(f"\nListing {root}:")
    if root.exists():
        for p in sorted(root.iterdir()):
            try:
                print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size} bytes")
            except Exception as e:
                print(" ", p, "stat_error", e)
    else:
        print(" missing")

# Deeper benchmark listing, including hidden and symlink info
b = Path("benchmark")
if b.exists():
    print("\nRecursive benchmark listing:")
    for p in sorted(b.rglob("*"))[:500]:
        try:
            print(" ", p, "->" if p.is_symlink() else "", os.readlink(p) if p.is_symlink() else "", "dir" if p.is_dir() else f"file {p.stat().st_size} bytes")
        except Exception as e:
            print(" ", p, "ERR", repr(e))

# Search for csv/pkl/xlsx/parquet in cwd (not too broad)
print("\nData-like files under cwd:")
for p in sorted(Path(".").rglob("*")):
    if p.is_file() and p.suffix.lower() in [".csv", ".pkl", ".pickle", ".xlsx", ".xls", ".parquet", ".tsv", ".json"]:
        print(" ", p, p.stat().st_size)

# Inspect benchmark files if any likely metadata exists
for p in sorted(Path(".").rglob("*")):
    if p.is_file() and p.stat().st_size < 200000 and p.suffix.lower() in [".py", ".txt", ".md", ".json", ".yaml", ".yml"]:
        print(f"\n--- {p} ---")
        try:
            print(p.read_text(errors="replace")[:4000])
        except Exception as e:
            print("read error", e)