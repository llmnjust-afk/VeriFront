#!/usr/bin/env python3
from pathlib import Path
import os
import numpy as np
import pandas as pd

print("Inspecting gold program/evaluator to infer exact expected output format...")
for p in [Path("benchmark/gold_programs/polynomial_fit.py"), Path("benchmark/eval_programs/eval_polynomial_fit.py"), Path("benchmark/eval_programs/gold_results/polynomial_fit_gold.csv")]:
    print(f"\n--- {p} exists={p.exists()} size={p.stat().st_size if p.exists() else 'NA'} ---")
    if p.exists():
        if p.suffix == ".csv":
            df = pd.read_csv(p)
            print(df.head())
            print(df.tail())
            print("shape:", df.shape, "columns:", list(df.columns))
            print("dtypes:", df.dtypes.to_dict())
            print("describe:")
            print(df.describe(include="all"))
        else:
            txt = p.read_text()
            print(txt[:4000])

print("\nInspecting NetCDF variables...")
import xarray as xr
ds = xr.open_dataset("polynomial_fit/A1B_north_america.nc")
print(ds)
for v in ds.variables:
    print(v, ds[v].dims, ds[v].shape, ds[v].dtype, dict(ds[v].attrs))
print("time sample:", ds["time"].values[:10], ds["time"].values[-10:])
if "air_temperature" in ds:
    arr = ds["air_temperature"]
    print("air_temperature shape/dims:", arr.shape, arr.dims)
    print("sample stats via xarray:", float(arr.mean()), float(arr.min()), float(arr.max()))