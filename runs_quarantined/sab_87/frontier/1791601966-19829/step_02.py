#!/usr/bin/env python3
from pathlib import Path
import os

print("Current working directory:", Path.cwd())
print("Top-level directory listing:")
for p in sorted(Path(".").iterdir()):
    try:
        if p.is_dir():
            print(f"DIR  {p}/")
        else:
            print(f"FILE {p} size={p.stat().st_size}")
    except Exception as e:
        print(f"ERR  {p}: {e}")

print("\nSearching for NetCDF-like files and polynomial_fit directories...")
matches = []
for root, dirs, files in os.walk("."):
    # limit excessive hidden/cache traversal
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".cache"}]
    for d in dirs:
        if "poly" in d.lower() or "fit" in d.lower():
            matches.append(str(Path(root) / d) + "/")
    for f in files:
        lf = f.lower()
        if lf.endswith((".nc", ".nc4", ".cdf", ".netcdf")) or "north" in lf or "america" in lf or "a1b" in lf:
            path = Path(root) / f
            matches.append(f"{path} size={path.stat().st_size}")
for m in matches[:200]:
    print(m)
print(f"Total matches shown/total: {min(len(matches),200)}/{len(matches)}")