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
    raise FileNotFoundError("sleep_data.pkl not found in expected locations")

t0 = time.time()
df = pd.read_pickle(data_path)
print(f"Loaded dataframe in {time.time()-t0:.2f}s")
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("Head:\n", df.head().to_string())
print("Tail:\n", df.tail().to_string())

# Determine sampling rate from timestamps
time_col = pd.to_datetime(df["time"])
dt = time_col.diff().dt.total_seconds().dropna()
median_dt = float(dt.median())
sampling_rate = 1.0 / median_dt
print("Time start:", time_col.iloc[0], "end:", time_col.iloc[-1])
print("Median dt:", median_dt, "sampling_rate:", sampling_rate)
print("dt quantiles:", dt.quantile([0, .01, .1, .5, .9, .99, 1]).to_dict())

acc = df[["acc_x", "acc_y", "acc_z"]].to_numpy(dtype=float, copy=True)
print("Acceleration array:", acc.shape, acc.dtype, "finite:", np.isfinite(acc).all())
print("Acc first row:", acc[0].tolist())

# Run BioPsyKit sleep processing pipeline as requested
t1 = time.time()
try:
    result = predict_pipeline_acceleration(acc, sampling_rate=sampling_rate, convert_to_g=True, epoch_length=60)
except Exception as e:
    print("Pipeline failed:", repr(e))
    traceback.print_exc()
    raise
print(f"Pipeline completed in {time.time()-t1:.2f}s")
print("Result type:", type(result), "keys:", list(result.keys()) if isinstance(result, dict) else None)

# Print concise summaries of all outputs
if isinstance(result, dict):
    for k, v in result.items():
        print("\nKEY:", k, "TYPE:", type(v))
        if isinstance(v, pd.DataFrame):
            print("shape:", v.shape)
            print("columns:", list(v.columns))
            print("head:\n", v.head().to_string())
            print("tail:\n", v.tail().to_string())
        elif isinstance(v, pd.Series):
            print(v.to_string())
        else:
            print(repr(v))

# Save raw-ish inspection output for next turn
Path("pred_results").mkdir(exist_ok=True)
summary = {
    "data_path": str(data_path),
    "shape": list(df.shape),
    "start_time": str(time_col.iloc[0]),
    "end_time": str(time_col.iloc[-1]),
    "median_dt": median_dt,
    "sampling_rate": sampling_rate,
    "result_keys": list(result.keys()) if isinstance(result, dict) else None,
}
with open("pred_results/imu_debug_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("Wrote pred_results/imu_debug_summary.json")