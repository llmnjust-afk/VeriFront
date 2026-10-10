#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

gold = Path("/data/lab/sab_data/benchmark_verified/benchmark/eval_programs/gold_results/polynomial_fit_gold.csv")
print("Gold CSV exists:", gold.exists(), "size:", gold.stat().st_size if gold.exists() else "NA")
if gold.exists():
    txt = gold.read_text()
    print("First 20 lines:")
    for line in txt.splitlines()[:20]:
        print(repr(line))
    print("Last 5 lines:")
    for line in txt.splitlines()[-5:]:
        print(repr(line))
    df = pd.read_csv(gold)
    print("shape", df.shape)
    print(df.head().to_string(index=False))
    print(df.tail().to_string(index=False))

# Also inspect raw numeric time values without xarray decoding
nc = Path("polynomial_fit/A1B_north_america.nc")
print("\nInspecting raw NetCDF numeric values from", nc)
try:
    import netCDF4
    ds = netCDF4.Dataset(nc, "r")
    t = ds.variables["time"]
    print("time units", getattr(t, "units", None), "calendar", getattr(t, "calendar", None))
    print("time raw first/last:", t[:5], t[-5:])
    temp = ds.variables["air_temperature"]
    print("temp shape", temp.shape)
    print("temp[0:5,0,0]:", temp[:5,0,0])
    print("temp[0,0,0:5]:", temp[0,0,0:5])
    ds.close()
except Exception as e:
    print("netCDF4 failed:", type(e).__name__, e)
    import xarray as xr
    ds = xr.open_dataset(nc, decode_times=False)
    print(ds)
    print("time attrs", ds["time"].attrs)
    print("time raw first/last", ds["time"].values[:5], ds["time"].values[-5:])
    print("temp[0:5,0,0]", ds["air_temperature"].values[:5,0,0])
    ds.close()