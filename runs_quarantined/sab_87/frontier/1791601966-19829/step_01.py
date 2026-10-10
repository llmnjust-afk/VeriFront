#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

print("Starting inspection of NetCDF dataset...")
path = Path("polynomial_fit/A1B_north_america.nc")
print(f"Dataset exists: {path.exists()} at {path}")
print(f"File size bytes: {path.stat().st_size if path.exists() else 'NA'}")

# Try available NetCDF readers
mods = {}
for name in ["netCDF4", "xarray", "scipy"]:
    try:
        __import__(name)
        mods[name] = True
    except Exception as e:
        mods[name] = False
        print(f"Could not import {name}: {type(e).__name__}: {e}")
print("Available modules:", mods)

if not path.exists():
    sys.exit("Dataset not found")

# Inspect using xarray if available, otherwise scipy.io.netcdf
if mods.get("xarray"):
    import xarray as xr
    ds = xr.open_dataset(path)
    print("\nXarray dataset summary:")
    print(ds)
    print("\nVariables and attrs:")
    for v in ds.variables:
        da = ds[v]
        print(f"VAR {v}: dims={da.dims}, shape={da.shape}, dtype={da.dtype}")
        print("  attrs:", dict(da.attrs))
    print("\nGlobal attrs:", dict(ds.attrs))
    # Print small time info
    if "time" in ds:
        t = ds["time"]
        print("time values first/last/min/max:", t.values[:5], t.values[-5:], t.values.min(), t.values.max())
elif mods.get("scipy"):
    from scipy.io import netcdf_file
    f = netcdf_file(str(path), "r", mmap=False)
    print("\nScipy netcdf dimensions:")
    print(f.dimensions)
    print("\nVariables:")
    for k, v in f.variables.items():
        print(f"VAR {k}: dimensions={v.dimensions}, shape={v.shape}, dtype={v.data.dtype}")
        print("  attrs:", {a: getattr(v, a) for a in dir(v) if not a.startswith("_") and a not in ["data", "dimensions", "shape", "typecode", "isrec", "itemsize"]})
    if "time" in f.variables:
        tv = f.variables["time"].data.copy()
        print("time values first/last/min/max:", tv[:5], tv[-5:], tv.min(), tv.max())
    f.close()
else:
    sys.exit("No NetCDF reader available")