#!/usr/bin/env python3
import os, json, inspect, time, warnings, sys
from pathlib import Path
import pandas as pd
import numpy as np

p = Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl")
print("Loading:", p)
df = pd.read_pickle(p)
idx = pd.to_datetime(df.index)
dt = pd.Series(idx).diff().dropna().dt.total_seconds()
fs = 1.0 / dt.median()
print("shape:", df.shape, "start:", idx[0], "end:", idx[-1], "fs:", fs)

from biopsykit.sleep import sleep_processing_pipeline
import biopsykit.sleep.sleep_processing_pipeline.sleep_processing_pipeline as spp
print("spp module:", spp.__file__)
for name in ["compute_sleep_endpoints"]:
    obj = getattr(spp, name, None)
    print("\n==", name, obj, "==")
    if obj is not None:
        try:
            print(inspect.getsource(obj)[:5000])
        except Exception as e:
            print("source err:", repr(e))

# Use DataFrame with acc columns because BioPsyKit convert_acc_data_to_g expects .filter(like="acc")
acc_df = df[["acc_x", "acc_y", "acc_z"]]
print("acc_df:", type(acc_df), acc_df.shape, acc_df.index[0], acc_df.index[-1])
print("Running BioPsyKit pipeline with DataFrame...")
t0 = time.time()
try:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = sleep_processing_pipeline.predict_pipeline_acceleration(acc_df, sampling_rate=fs, convert_to_g=True)
        print("warnings:", len(w))
        for ww in w[:20]:
            print("WARNING:", str(ww.message))
    print("Pipeline completed in", time.time()-t0, "s")
    print("Result keys:", list(result.keys()) if isinstance(result, dict) else None)
    if isinstance(result, dict):
        for k, v in result.items():
            print("\nKEY", k, "TYPE", type(v))
            if isinstance(v, pd.DataFrame):
                print("shape", v.shape, "cols", v.columns.tolist(), "index type", type(v.index), "index head/tail", (v.index[0] if len(v) else None), (v.index[-1] if len(v) else None))
                print("head:\n", v.head().to_string())
                print("tail:\n", v.tail().to_string())
            else:
                print(repr(v)[:3000])
        endpoints = result.get("sleep_endpoints", {})
        print("\nENDPOINTS:", repr(endpoints))
except Exception as e:
    print("PIPELINE ERROR:", type(e).__name__, repr(e))
    import traceback
    traceback.print_exc()