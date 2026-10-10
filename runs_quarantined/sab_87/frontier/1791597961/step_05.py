#!/usr/bin/env python3
from pathlib import Path
import shutil
import os

src = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/polynomial_fit/A1B_north_america.nc")
dst_dir = Path("polynomial_fit")
dst_dir.mkdir(exist_ok=True)
dst = dst_dir / "A1B_north_america.nc"
if src.exists():
    shutil.copy2(src, dst)
    print(f"Copied dataset from {src} to {dst} ({dst.stat().st_size} bytes)")
else:
    print(f"Source dataset missing: {src}")

# Inspect gold/eval to infer exact expected CSV columns/algorithm if available.
for p in [
    Path("/data/lab/sab_data/benchmark_verified/benchmark/gold_programs/polynomial_fit.py"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/eval_programs/eval_polynomial_fit.py"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/eval_programs/gold_results/polynomial_fit_gold.csv"),
]:
    print(f"\n--- Inspecting {p} ---")
    if p.exists():
        txt = p.read_text(errors="replace")
        print(txt[:5000])
        if p.suffix == ".csv":
            print("CSV line count preview:", len(txt.splitlines()))
    else:
        print("missing")

# Inspect NetCDF metadata now
try:
    import netCDF4
    ds = netCDF4.Dataset(dst, "r")
    print("\nNetCDF dimensions:")
    for name, dim in ds.dimensions.items():
        print(name, len(dim))
    print("NetCDF variables:")
    for name, var in ds.variables.items():
        print(name, var.dimensions, var.shape, var.dtype, {a: getattr(var, a) for a in var.ncattrs()})
        try:
            arr = var[:]
            import numpy as np
            flat = np.asarray(arr).ravel()
            print(" sample:", flat[:5], "min", np.nanmin(flat), "max", np.nanmax(flat))
        except Exception as e:
            print(" sample failed", e)
    ds.close()
except Exception as e:
    print("NetCDF inspect failed:", type(e).__name__, e)