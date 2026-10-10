#!/usr/bin/env python3
from pathlib import Path
import os

print("Inspecting benchmark and nearby directories for data...")
for base in [Path("benchmark"), Path("pred_results"), Path("/data/lab/VeriFront/runs/sab_87/frontier"), Path("/data/lab/VeriFront")]:
    print(f"\nListing {base}: exists={base.exists()}")
    if base.exists():
        count = 0
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".cache"}]
            depth = len(Path(root).relative_to(base).parts) if root != str(base) else 0
            if depth > 3:
                dirs[:] = []
                continue
            indent = "  " * depth
            print(f"{indent}{Path(root).name}/")
            for f in files[:20]:
                p = Path(root)/f
                print(f"{indent}  {f} size={p.stat().st_size}")
            if len(files) > 20:
                print(f"{indent}  ... {len(files)-20} more files")
            count += 1
            if count > 100:
                print("  ... stopping listing after 100 dirs")
                break

print("\nBroader search under /data/lab for .nc files (depth/quantity limited)...")
found = []
for root, dirs, files in os.walk("/data/lab"):
    # prune many likely irrelevant dirs
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".cache", "node_modules"}]
    for f in files:
        lf = f.lower()
        if lf.endswith((".nc", ".nc4", ".cdf", ".netcdf")) or f == "A1B_north_america.nc":
            p = Path(root)/f
            try:
                found.append((str(p), p.stat().st_size))
            except Exception:
                found.append((str(p), None))
    if len(found) >= 50:
        break
print(f"Found {len(found)} candidate files:")
for p, s in found[:50]:
    print(p, "size=", s)