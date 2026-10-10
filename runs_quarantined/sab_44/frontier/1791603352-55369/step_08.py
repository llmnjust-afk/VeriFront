#!/usr/bin/env python3
import json, time, warnings
from pathlib import Path
import pandas as pd
import numpy as np

from biopsykit.sleep import sleep_processing_pipeline

p = Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl")
df = pd.read_pickle(p)
idx = pd.to_datetime(df.index)
dt = pd.Series(idx).diff().dropna().dt.total_seconds()
fs = 1.0 / dt.median()
print(f"Loaded {df.shape}, start={idx[0]}, end={idx[-1]}, fs={fs:.9f}")

acc_df = df[["acc_x", "acc_y", "acc_z"]]
print("Running recommended BioPsyKit predict_pipeline_acceleration...")
t0 = time.time()
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    result = sleep_processing_pipeline.predict_pipeline_acceleration(acc_df, sampling_rate=fs, convert_to_g=True)
print(f"Pipeline done in {time.time()-t0:.2f}s; warnings={len(w)}")
print("Result keys:", list(result.keys()))

endpoints = result.get("sleep_endpoints", {})
print("Raw sleep_endpoints type:", type(endpoints))
print("Raw sleep_endpoints repr:", repr(endpoints))

# Print concise summaries of intermediate outputs
for key in ["major_wear_block", "bed_interval"]:
    print(key, "=", repr(result.get(key)))
for key in ["activity_counts", "sleep_wake_prediction", "rest_periods"]:
    v = result.get(key)
    if isinstance(v, pd.DataFrame):
        print(f"{key}: shape={v.shape}, cols={v.columns.tolist()}, index_start={v.index[0] if len(v) else None}, index_end={v.index[-1] if len(v) else None}")
        print(v.head(3).to_string())
        print(v.tail(3).to_string())

# Extract required keys and JSON-serialize.
required = ["sleep_onset", "wake_onset", "total_sleep_duration"]
out = {}
for k in required:
    val = endpoints[k]
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        out[k] = str(pd.Timestamp(val))
    elif isinstance(val, pd.Timedelta):
        out[k] = val.total_seconds()
    elif isinstance(val, np.generic):
        out[k] = val.item()
    else:
        out[k] = val

Path("pred_results").mkdir(exist_ok=True)
out_path = Path("pred_results/imu_pred.json")
with out_path.open("w") as f:
    json.dump(out, f, indent=2)
print("Saved:", out_path.resolve())
print(out_path.read_text())