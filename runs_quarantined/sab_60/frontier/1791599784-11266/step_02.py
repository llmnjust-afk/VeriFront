#!/usr/bin/env python3
import os
from pathlib import Path

print("cwd", os.getcwd())
print("Top-level files/dirs:")
for p in sorted(Path(".").iterdir()):
    print(p, "DIR" if p.is_dir() else f"FILE {p.stat().st_size}")

# Search nearby for nvc/Ragni2016.csv without being too huge
candidates = [Path("."), Path(".."), Path("../.."), Path("../../.."), Path("/data/lab/VeriFront")]
for base in candidates:
    print("\nSearching under", base)
    try:
        hits = []
        for p in base.rglob("Ragni2016.csv"):
            hits.append(p)
            print("HIT", p)
            if len(hits) >= 20:
                print("stopping at 20 hits")
                break
        if hits:
            break
    except Exception as e:
        print("search error", base, repr(e))