#!/usr/bin/env python3
from pathlib import Path
import os

print("Current working directory:", Path.cwd())
print("Top-level entries:")
for p in sorted(Path(".").iterdir()):
    try:
        print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size} bytes")
    except Exception as e:
        print(" ", p, "?", e)

print("\nSearching for NetCDF files and polynomial_fit directories under current tree...")
for p in Path(".").rglob("*"):
    if p.name == "polynomial_fit" or p.suffix.lower() in [".nc", ".cdf", ".netcdf"]:
        try:
            print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size} bytes")
        except Exception as e:
            print(" ", p, "?", e)

print("\nSearching nearby /data/lab/VeriFront if accessible (limited)...")
base = Path("/data/lab/VeriFront")
if base.exists():
    count = 0
    for p in base.rglob("A1B_north_america.nc"):
        print("FOUND:", p, p.stat().st_size, "bytes")
        count += 1
        if count >= 20:
            break
    print("Found count (limited):", count)
else:
    print("/data/lab/VeriFront not present")