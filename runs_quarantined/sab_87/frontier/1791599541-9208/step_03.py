#!/usr/bin/env python3
from pathlib import Path
import shutil

src = Path("/data/lab/VeriFront/runs/sab_87/frontier/1791597961/polynomial_fit/A1B_north_america.nc")
dst_dir = Path("polynomial_fit")
dst = dst_dir / "A1B_north_america.nc"
dst_dir.mkdir(exist_ok=True)
if not dst.exists():
    print(f"Copying dataset from {src} to {dst}")
    shutil.copy2(src, dst)
else:
    print(f"Dataset already present at {dst}")

print("Inspecting dataset...")
try:
    import xarray as xr
    ds = xr.open_dataset(dst)
    print(ds)
    print("\nData variables:")
    for name, var in ds.data_vars.items():
        print(f"- {name}: dims={var.dims}, shape={var.shape}, dtype={var.dtype}, attrs={dict(var.attrs)}")
    print("\nCoordinates:")
    for name, coord in ds.coords.items():
        vals_preview = coord.values[:5] if coord.ndim == 1 and coord.size >= 5 else coord.values
        print(f"- {name}: dims={coord.dims}, shape={coord.shape}, dtype={coord.dtype}, attrs={dict(coord.attrs)}, preview={vals_preview}")
    if "time" in ds:
        print("\ntime attrs:", dict(ds["time"].attrs))
        print("time first/last:", ds["time"].values[:3], ds["time"].values[-3:])
    if "air_temperature" in ds:
        v = ds["air_temperature"]
        print("\nair_temperature sample attrs:", dict(v.attrs))
        print("sample values:", v.values.reshape(-1)[:10])
    ds.close()
except Exception as e:
    print("xarray failed", type(e).__name__, e)
    from scipy.io import netcdf_file
    nc = netcdf_file(str(dst), "r")
    print("Dimensions:", nc.dimensions)
    print("Variables:", list(nc.variables.keys()))
    for name, var in nc.variables.items():
        print(name, var.dimensions, var.shape, var.data.dtype)
        print(" attrs:", getattr(var, "_attributes", {}))
    nc.close()