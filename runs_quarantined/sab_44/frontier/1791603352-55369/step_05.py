#!/usr/bin/env python3
import os, json, inspect, time
from pathlib import Path
import pandas as pd
import numpy as np

p = Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl")
print("Loading:", p, "size", p.stat().st_size)
t0 = time.time()
df = pd.read_pickle(p)
print("Loaded in", time.time()-t0, "s")
print("Type:", type(df), "shape:", getattr(df, "shape", None))
print("Columns:", df.columns.tolist())
print("Dtypes:\n", df.dtypes)
print("Memory MB:", df.memory_usage(deep=True).sum()/1e6)
print("Head:\n", df.head().to_string())
print("Tail:\n", df.tail().to_string())

# Time and sampling
time_col = "time" if "time" in df.columns else None
if time_col:
    tt = pd.to_datetime(df[time_col])
else:
    tt = pd.to_datetime(df.index)
print("Time start/end:", tt.iloc[0], tt.iloc[-1])
print("Total recording duration:", tt.iloc[-1] - tt.iloc[0])
dt = tt.diff().dropna().dt.total_seconds()
print("dt stats:\n", dt.describe(percentiles=[.001,.01,.05,.5,.95,.99,.999]).to_string())
fs = 1.0 / dt.median()
print("median sampling rate:", fs)

# Inspect compute endpoint implementation
from biopsykit.sleep import sleep_processing_pipeline
try:
    print("\ncompute_sleep_endpoints source:\n", inspect.getsource(sleep_processing_pipeline.compute_sleep_endpoints))
except Exception as e:
    print("Could not inspect compute_sleep_endpoints:", repr(e))

# Quick check for invalid values and basic ranges
acc_cols = [c for c in df.columns if c.startswith("acc")]
gyr_cols = [c for c in df.columns if c.startswith("gyr")]
print("acc_cols", acc_cols, "gyr_cols", gyr_cols)
for cols in [acc_cols, gyr_cols]:
    if cols:
        vals = df[cols].astype(float)
        print(cols, "nan count", vals.isna().sum().to_dict())
        print(vals.describe().to_string())