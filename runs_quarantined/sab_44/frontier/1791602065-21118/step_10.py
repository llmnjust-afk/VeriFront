#!/usr/bin/env python3
import json
import time
from pathlib import Path

import pandas as pd
from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration

# Locate the dataset robustly.
candidates = [
    Path("sleep_imu_data/sleep_data.pkl"),
    Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/sleep_imu_data/sleep_data.pkl"),
]
data_path = next((p for p in candidates if p.exists()), None)
if data_path is None:
    raise FileNotFoundError("Could not locate sleep_imu_data/sleep_data.pkl")
print("Using data:", data_path)

# Load IMU dataframe. In the provided pickle, time is the DatetimeIndex.
t0 = time.time()
df = pd.read_pickle(data_path)
time_index = pd.to_datetime(df.index if "time" not in df.columns else df["time"])
median_dt = float(pd.Series(time_index).diff().dt.total_seconds().dropna().median())
sampling_rate = 1.0 / median_dt
print(f"Loaded {df.shape[0]} samples in {time.time() - t0:.2f}s")
print("Start:", time_index[0], "End:", time_index[-1])
print("Median dt:", median_dt, "Sampling rate:", sampling_rate)

# Run the benchmark-specified BioPsyKit acceleration sleep processing pipeline.
# BioPsyKit 0.9.0 expects a DataFrame with acc_* columns for convert_to_g=True.
acc_df = df[["acc_x", "acc_y", "acc_z"]].copy()
t1 = time.time()
pipeline_result = predict_pipeline_acceleration(
    acc_df,
    sampling_rate=sampling_rate,
    convert_to_g=True,
    epoch_length=60,
)
print(f"Pipeline finished in {time.time() - t1:.2f}s")
print("Pipeline keys:", list(pipeline_result.keys()))

sleep_endpoints = pipeline_result["sleep_endpoints"]
print("Sleep endpoints returned by BioPsyKit:")
for key in ["sleep_onset", "wake_onset", "total_sleep_duration"]:
    print(f"  {key}: {sleep_endpoints[key]!r}")

# Save only the required three endpoints.
out = {
    "sleep_onset": str(sleep_endpoints["sleep_onset"]),
    "wake_onset": str(sleep_endpoints["wake_onset"]),
    "total_sleep_duration": int(sleep_endpoints["total_sleep_duration"]),
}
out_path = Path("pred_results/imu_pred.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w") as f:
    json.dump(out, f, indent=2)

print("Wrote:", out_path)
print(json.dumps(out, indent=2))