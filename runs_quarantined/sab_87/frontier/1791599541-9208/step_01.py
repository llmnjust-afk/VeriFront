#!/usr/bin/env python3
import os
from pathlib import Path

print("Starting inspection of NetCDF dataset...")
path = Path("polynomial_fit/A1B_north_america.nc")
print(f"Dataset exists: {path.exists()} at {path}")

if not path.exists():
    raise FileNotFoundError(path)

# Try xarray first, then netCDF4 if needed
try:
    import xarray as xr
    print("Using xarray")
    ds = xr.open_dataset(path)
    print(ds)
    print("\nVariables:")
    for name in ds.variables:
        var = ds[name]
        print(f"- {name}: dims={var.dims}, shape={var.shape}, attrs={dict(var.attrs)}")
    print("\nCoordinates:")
    for name in ds.coords:
        coord = ds[name]
        print(f"- {name}: dims={coord.dims}, shape={coord.shape}, attrs={dict(coord.attrs)}")
    ds.close()
except Exception as e:
    print(f"xarray inspection failed: {type(e).__name__}: {e}")
    try:
        from netCDF4 import Dataset
        print("Using netCDF4")
        nc = Dataset(path, "r")
        print("Dimensions:")
        for name, dim in nc.dimensions.items():
            print(f"- {name}: size={len(dim)}, unlimited={dim.isunlimited()}")
        print("Variables:")
        for name, var in nc.variables.items():
            print(f"- {name}: dimensions={var.dimensions}, shape={var.shape}, dtype={var.dtype}")
            print(f"  attrs={ {attr: getattr(var, attr) for attr in var.ncattrs()} }")
        nc.close()
    except Exception as e2:
        print(f"netCDF4 inspection failed: {type(e2).__name__}: {e2}")
        raise