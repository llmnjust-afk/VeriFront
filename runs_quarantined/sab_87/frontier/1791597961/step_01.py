#!/usr/bin/env python3
import os
from pathlib import Path

nc_path = Path("polynomial_fit/A1B_north_america.nc")
print(f"Checking dataset: {nc_path.resolve()}")
print(f"Exists: {nc_path.exists()}, size: {nc_path.stat().st_size if nc_path.exists() else 'NA'} bytes")

# Try to inspect with available libraries
try:
    import netCDF4
    print("netCDF4 available")
    ds = netCDF4.Dataset(nc_path, "r")
    print("Dimensions:")
    for name, dim in ds.dimensions.items():
        print(f"  {name}: size={len(dim)}, unlimited={dim.isunlimited()}")
    print("Variables:")
    for name, var in ds.variables.items():
        print(f"  {name}: dimensions={var.dimensions}, shape={var.shape}, dtype={var.dtype}")
        attrs = {a: getattr(var, a) for a in var.ncattrs()}
        print(f"    attrs={attrs}")
    print("Global attrs:")
    print({a: getattr(ds, a) for a in ds.ncattrs()})
    ds.close()
except Exception as e:
    print(f"netCDF4 inspection failed: {type(e).__name__}: {e}")
    try:
        import xarray as xr
        print("xarray available")
        ds = xr.open_dataset(nc_path)
        print(ds)
        print("attrs:", ds.attrs)
        ds.close()
    except Exception as e2:
        print(f"xarray inspection failed: {type(e2).__name__}: {e2}")