#!/usr/bin/env python3
import os, json, inspect, time, warnings
from pathlib import Path
import pandas as pd
import numpy as np

p = Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl")
print("Loading:", p, "size", p.stat().st_size)
t0 = time.time()
df = pd.read_pickle(p)
print("Loaded in", time.time()-t0, "s")
print("shape:", df.shape, "columns:", df.columns.tolist())

idx = pd.to_datetime(df.index)
print("Index type:", type(idx))
print("Time start/end:", idx[0], idx[-1])
print("Total recording duration:", idx[-1] - idx[0])
dt = pd.Series(idx).diff().dropna().dt.total_seconds()
print("dt stats:\n", dt.describe(percentiles=[.001,.01,.05,.5,.95,.99,.999]).to_string())
fs = 1.0 / dt.median()
print("median sampling rate:", fs)
print("unique-ish dt top counts:")
print(dt.round(6).value_counts().head(10).to_string())

from biopsykit.sleep import sleep_processing_pipeline
print("pipeline signature:", inspect.signature(sleep_processing_pipeline.predict_pipeline_acceleration))
for name in ["compute_sleep_endpoints", "ActivityCounts", "WearDetection", "RestPeriods", "SleepWakeDetection"]:
    obj = getattr(sleep_processing_pipeline, name, None)
    print("\n==", name, "==")
    if obj is not None:
        try:
            print(inspect.signature(obj))
        except Exception as e:
            print("sig err", repr(e))
        try:
            src = inspect.getsource(obj)
            print(src[:5000])
        except Exception as e:
            print("src err", repr(e))

acc_cols = ["acc_x", "acc_y", "acc_z"]
acc = df[acc_cols].to_numpy(dtype=float, copy=False)
print("acc ndarray shape", acc.shape, "dtype", acc.dtype)
print("acc finite:", np.isfinite(acc).all())
print("acc first rows:", acc[:3])
print("acc magnitude quantiles:", pd.Series(np.sqrt((acc**2).sum(axis=1))).quantile([0,.01,.05,.5,.95,.99,1]).to_dict())

# Try the benchmark-recommended BioPsyKit pipeline.
# Data are in m/s^2 per preview, so leave convert_to_g=True.
print("\nRunning predict_pipeline_acceleration...")
t0 = time.time()
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    result = sleep_processing_pipeline.predict_pipeline_acceleration(acc, sampling_rate=fs, convert_to_g=True)
    print("Pipeline warnings:", len(w))
    for ww in w[:20]:
        print("WARNING:", str(ww.message))
print("Pipeline completed in", time.time()-t0, "s")
print("Result type:", type(result), "keys:", list(result.keys()) if isinstance(result, dict) else None)
if isinstance(result, dict):
    for k, v in result.items():
        if isinstance(v, pd.DataFrame):
            print(f"\n[{k}] DataFrame shape={v.shape} columns={v.columns.tolist()}")
            print(v.head().to_string())
            print(v.tail().to_string())
        else:
            print(f"\n[{k}] {type(v)}: {repr(v)[:2000]}")
    endpoints = result.get("sleep_endpoints", {})
    print("sleep_endpoints repr:", repr(endpoints))