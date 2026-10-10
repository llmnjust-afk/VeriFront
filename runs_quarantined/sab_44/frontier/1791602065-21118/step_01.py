#!/usr/bin/env python3
import os, json, pickle, sys, importlib.util
from pathlib import Path

print("Working directory:", os.getcwd())
data_path = Path("sleep_imu_data/sleep_data.pkl")
print("Data exists:", data_path.exists(), "size:", data_path.stat().st_size if data_path.exists() else None)

print("Checking key packages...")
for pkg in ["biopsykit", "sleep_processing_pipeline", "pandas", "numpy", "scipy"]:
    spec = importlib.util.find_spec(pkg)
    print(pkg, "FOUND" if spec else "not found")

if data_path.exists():
    import pandas as pd
    obj = pd.read_pickle(data_path)
    print("Loaded type:", type(obj))
    if hasattr(obj, "shape"):
        print("Shape:", obj.shape)
    print("Head:")
    print(obj.head().to_string())
    print("Tail:")
    print(obj.tail().to_string())
    print("Dtypes:")
    print(obj.dtypes if hasattr(obj, "dtypes") else "no dtypes")
    if hasattr(obj, "columns") and "time" in obj.columns:
        t = pd.to_datetime(obj["time"])
        print("Time start:", t.iloc[0], "end:", t.iloc[-1])
        print("Duration seconds:", (t.iloc[-1] - t.iloc[0]).total_seconds())
        print("Timezone:", getattr(t.dt, "tz", None))
        dt = t.diff().dt.total_seconds().dropna()
        print("dt stats:", dt.describe(percentiles=[.01,.05,.5,.95,.99]).to_string())
    if hasattr(obj, "describe"):
        print("Numeric describe:")
        print(obj.describe().to_string())