#!/usr/bin/env python3
import os
from pathlib import Path

for target in ["benchmark", "/data/lab/VeriFront/runs/sab_45/frontier/1791598145/benchmark", "/data/lab/VeriFront/runs/sab_45", "/data/lab/VeriFront"]:
    p = Path(target)
    print(f"\nInspecting {p} exists={p.exists()} is_dir={p.is_dir()} is_symlink={p.is_symlink()}")
    try:
        if p.exists() and p.is_dir():
            entries = list(p.iterdir())
            print(" entries:", len(entries))
            for e in entries[:100]:
                print("  -", e, "dir" if e.is_dir() else "file", "symlink" if e.is_symlink() else "")
    except Exception as e:
        print(" error:", repr(e))

print("\nFind pkl/csv/parquet/xlsx files under /data/lab/VeriFront/runs/sab_45 (max 200):")
base = Path("/data/lab/VeriFront/runs/sab_45")
n = 0
try:
    for pattern in ["*.pkl", "*.pickle", "*.csv", "*.parquet", "*.xlsx"]:
        for m in base.rglob(pattern):
            print(m)
            n += 1
            if n >= 200:
                raise StopIteration
except StopIteration:
    print("... truncated")
except Exception as e:
    print("search error:", repr(e))
print("printed", n)

print("\nEnvironment variables likely paths:")
for k, v in sorted(os.environ.items()):
    if any(s in k.lower() for s in ["data", "bench", "input", "path"]) or any(s in v.lower() for s in ["data", "bench", "input"]):
        print(k, "=", v)