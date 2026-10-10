#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd

print("Files in pred_results:")
for p in Path("pred_results").iterdir():
    print(p, p.stat().st_size)

debug_path = Path("pred_results/imu_debug_pipeline.json")
print("\nReading", debug_path)
txt = debug_path.read_text()
print("Length:", len(txt))
debug = json.loads(txt)
print("Top-level keys:", list(debug.keys()))
for k in ["major_wear_block", "bed_interval", "sleep_endpoints", "rest_periods", "sleep_wake_prediction", "activity_counts"]:
    print("\n==", k, "==")
    v = debug.get(k)
    if isinstance(v, str):
        print(v[:3000])
    else:
        print(json.dumps(v, indent=2)[:3000])

# Re-run pipeline only if needed, print sleep endpoints precisely and create JSON if possible.
from biopsykit.sleep.sleep_processing_pipeline import predict_pipeline_acceleration
data_path = Path("benchmark/datasets/sleep_imu_data/sleep_data.pkl")
df = pd.read_pickle(data_path)
time_index = pd.to_datetime(df.index)
sampling_rate = 1.0 / float(pd.Series(time_index).diff().dt.total_seconds().dropna().median())
result = predict_pipeline_acceleration(df[["acc_x","acc_y","acc_z"]].copy(), sampling_rate=sampling_rate, convert_to_g=True, epoch_length=60)
print("\nPrecise result entries:")
for key in ["bed_interval", "sleep_endpoints"]:
    val = result[key]
    print(key, type(val), repr(val))
    if isinstance(val, pd.DataFrame):
        print(val.to_string())
    elif isinstance(val, pd.Series):
        print(val.to_string())

se = result["sleep_endpoints"]
print("\nsleep_endpoints dict/items if possible:")
if hasattr(se, "items"):
    for k, v in se.items():
        print(repr(k), type(v), repr(v), str(v))