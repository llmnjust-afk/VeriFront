#!/usr/bin/env python3
from pathlib import Path
import os

print("cwd", Path.cwd())
print("top-level entries:")
for p in sorted(Path(".").iterdir()):
    print(" ", p.name, "dir" if p.is_dir() else "file", p.stat().st_size)

print("\nSearching for Ragni2016.csv and nvc directories nearby...")
candidates = []
for base in [Path("."), Path(".."), Path("../.."), Path("../../.."), Path("/data/lab/VeriFront")]:
    if base.exists():
        try:
            for p in base.rglob("Ragni2016.csv"):
                candidates.append(p)
                print("Ragni:", p)
        except Exception as e:
            print("Search error in", base, repr(e))

print("\nSearching for directories named nvc (limited display)...")
count = 0
for base in [Path("."), Path(".."), Path("../.."), Path("../../.."), Path("/data/lab/VeriFront")]:
    if base.exists():
        try:
            for p in base.rglob("nvc"):
                if p.is_dir():
                    print("nvc dir:", p)
                    count += 1
                    if count >= 20:
                        raise SystemExit
        except SystemExit:
            break
        except Exception as e:
            print("Dir search error in", base, repr(e))
print("done, candidates", len(candidates))