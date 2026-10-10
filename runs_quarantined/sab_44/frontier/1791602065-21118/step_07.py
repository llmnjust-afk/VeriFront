#!/usr/bin/env python3
import os, json, time, traceback
from pathlib import Path
import pandas as pd
import numpy as np
from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration

# Locate dataset
candidates = [
    Path("sleep_imu_data/sleep_data.pkl"),
    Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/sleep_imu_data/sleep_data.pkl"),
]
data_path = next((p for p in candidates if p.exists()), None)
print("Selected data path:", data_path)
if data_path is None:
    raise FileNotFoundError("sleep_data.pkl not found")

t0 = time.time()
df = pd.read_pickle(data_path)
print(f"Loaded dataframe in {time.time()-t0:.2f}s")
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("Index:", type(df.index), df.index.name, df.index.dtype)
print("Head:\n", df.head().to_string())
print("Tail:\n", df.tail().to_string())

# Time is the DataFrame index in this pickle
if "time" in df.columns:
    time_col = pd.to_datetime(df["time"])
else:
    time_col = pd.to_datetime(df.index)
dt = pd.Series(time_col).diff().dt.total_seconds().dropna()
median_dt = float(dt.median())
sampling_rate = 1.0 / median_dt
print("Time start:", time_col[0], "end:", time_col[-1])
print("Median dt:", median_dt, "sampling_rate:", sampling_rate)
print("dt describe:", dt.describe(percentiles=[.01,.05,.5,.95,.99]).to_string())

acc = df[["acc_x", "acc_y", "acc_z"]].to_numpy(dtype=float, copy=True)
print("Acceleration array:", acc.shape, acc.dtype, "finite:", bool(np.isfinite(acc).all()))
print("Acc norm stats:", pd.Series(np.linalg.norm(acc, axis=1)).describe(percentiles=[.01,.05,.5,.95,.99]).to_string())

t1 = time.time()
try:
    result = predict_pipeline_acceleration(acc, sampling_rate=sampling_rate, convert_to_g=True, epoch_length=60)
except Exception as e:
    print("Pipeline failed:", repr(e))
    traceback.print_exc()
    raise
print(f"Pipeline completed in {time.time()-t1:.2f}s")
print("Result type:", type(result), "keys:", list(result.keys()) if isinstance(result, dict) else None)

Path("pred_results").mkdir(exist_ok=True)

# Summaries and serialize useful outputs for inspection
debug = {
    "data_path": str(data_path),
    "shape": list(df.shape),
    "start_time": str(time_col[0]),
    "end_time": str(time_col[-1]),
    "median_dt": median_dt,
    "sampling_rate": sampling_rate,
    "result_keys": list(result.keys()) if isinstance(result, dict) else None,
}
if isinstance(result, dict):
    for k, v in result.items():
        print("\nKEY:", k, "TYPE:", type(v))
        if isinstance(v, pd.DataFrame):
            print("shape:", v.shape, "columns:", list(v.columns))
            print("head:\n", v.head(10).to_string())
            print("tail:\n", v.tail(10).to_string())
            debug[k] = {
                "type": "DataFrame",
                "shape": list(v.shape),
                "columns": list(map(str, v.columns)),
                "head": v.head(5).astype(str).to_dict(orient="list"),
                "tail": v.tail(5).astype(str).to_dict(orient="list"),
            }
        elif isinstance(v, pd.Series):
            print(v.to_string())
            debug[k] = v.astype(str).to_dict()
        else:
            print(repr(v))
            try:
                json.dumps(v)
                debug[k] = v
            except TypeError:
                debug[k] = str(v)

with open("pred_results/imu_debug_summary.json", "w") as f:
    json.dump(debug, f, indent=2)
print("Wrote pred_results/imu_debug_summary.json")

# If pipeline already provides sleep_endpoints, try saving provisional answer too
if isinstance(result, dict) and "sleep_endpoints" in result and result["sleep_endpoints"] is not None:
    se = result["sleep_endpoints"]
    print("sleep_endpoints object:", type(se), repr(se))