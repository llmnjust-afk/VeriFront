#!/usr/bin/env python3
import os, json, time, traceback
from pathlib import Path
import pandas as pd
import numpy as np
from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration

candidates = [
    Path("sleep_imu_data/sleep_data.pkl"),
    Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/sleep_imu_data/sleep_data.pkl"),
]
data_path = next((p for p in candidates if p.exists()), None)
print("Selected data path:", data_path)
df = pd.read_pickle(data_path)
time_index = pd.to_datetime(df.index if "time" not in df.columns else df["time"])
dt = pd.Series(time_index).diff().dt.total_seconds().dropna()
sampling_rate = 1.0 / float(dt.median())
print("Shape:", df.shape, "sampling_rate:", sampling_rate, "start:", time_index[0], "end:", time_index[-1])

# BioPsyKit 0.9.0 convert_acc_data_to_g expects a DataFrame with acc-named columns.
acc_df = df[["acc_x", "acc_y", "acc_z"]].copy()
print("Input to pipeline:", type(acc_df), acc_df.shape, acc_df.dtypes.to_dict())

t1 = time.time()
try:
    result = predict_pipeline_acceleration(acc_df, sampling_rate=sampling_rate, convert_to_g=True, epoch_length=60)
except Exception as e:
    print("Pipeline failed:", repr(e))
    traceback.print_exc()
    raise
print(f"Pipeline completed in {time.time()-t1:.2f}s")
print("Result keys:", list(result.keys()) if isinstance(result, dict) else None)

Path("pred_results").mkdir(exist_ok=True)
debug = {"sampling_rate": sampling_rate, "result_keys": list(result.keys()) if isinstance(result, dict) else None}

for k, v in result.items():
    print("\nKEY:", k, "TYPE:", type(v))
    if isinstance(v, pd.DataFrame):
        print("shape:", v.shape, "columns:", list(v.columns), "index:", type(v.index), getattr(v.index, "dtype", None))
        print("head:\n", v.head(10).to_string())
        print("tail:\n", v.tail(10).to_string())
        debug[k] = {
            "type": "DataFrame",
            "shape": list(v.shape),
            "columns": list(map(str, v.columns)),
            "head": v.head(10).astype(str).to_dict(orient="list"),
            "tail": v.tail(10).astype(str).to_dict(orient="list"),
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

with open("pred_results/imu_debug_pipeline.json", "w") as f:
    json.dump(debug, f, indent=2)
print("Wrote pred_results/imu_debug_pipeline.json")