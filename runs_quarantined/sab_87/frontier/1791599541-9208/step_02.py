#!/usr/bin/env python3
from pathlib import Path
import os

print("Working directory:", Path.cwd())
print("Top-level entries:")
for p in sorted(Path(".").iterdir()):
    print(" -", p, "dir" if p.is_dir() else "file", p.stat().st_size if p.is_file() else "")

print("\nSearching for NetCDF files and polynomial_fit directories nearby...")
roots = [Path("."), Path(".."), Path("/data/lab/VeriFront/runs/sab_87/frontier")]
seen = set()
for root in roots:
    if root.exists():
        try:
            for p in root.rglob("*"):
                if p in seen:
                    continue
                seen.add(p)
                name = p.name.lower()
                if name.endswith((".nc", ".nc4", ".cdf")) or p.name == "polynomial_fit":
                    try:
                        rel = p.resolve()
                    except Exception:
                        rel = p
                    print("FOUND:", rel, "dir" if p.is_dir() else "file")
        except Exception as e:
            print(f"Search error under {root}: {type(e).__name__}: {e}")

print("\nDone search.")