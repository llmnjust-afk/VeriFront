#!/usr/bin/env python3
import os
from pathlib import Path
import pickle
import importlib

import pandas as pd
import numpy as np

data_dir = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/ecg_processing_data")
print("Using data dir:", data_dir)
print("Exists:", data_dir.exists())
print("Listing:", [p.name for p in data_dir.iterdir()])

fs = float((data_dir / "sampling_rate.txt").read_text().strip())
print("Sampling rate:", fs)

pkl_path = data_dir / "ecg_data.pkl"
try:
    obj = pd.read_pickle(pkl_path)
    print("Loaded pickle with pandas. Type:", type(obj))
except Exception as e:
    print("pandas read_pickle failed:", repr(e))
    with open(pkl_path, "rb") as f:
        obj = pickle.load(f)
    print("Loaded pickle with pickle. Type:", type(obj))

if isinstance(obj, pd.DataFrame):
    df = obj.copy()
elif isinstance(obj, pd.Series):
    df = obj.to_frame()
else:
    print("Object repr:", repr(obj)[:1000])
    raise SystemExit("Unsupported pickle object type")

print("DataFrame shape:", df.shape)
print("Columns:", list(df.columns))
print("Index type:", type(df.index), "index name:", df.index.name)
print("Head:")
print(df.head())
print("Tail:")
print(df.tail())
print("dtypes:")
print(df.dtypes)
print("NaNs per column:")
print(df.isna().sum())

# determine ECG series and time
if "ecg" in df.columns:
    ecg = pd.to_numeric(df["ecg"], errors="coerce")
else:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise SystemExit("No numeric ECG column found")
    ecg = pd.to_numeric(df[numeric_cols[0]], errors="coerce")
print("ECG stats:")
print(ecg.describe())
print("ECG first values:", ecg.head(10).tolist())

if "time" in df.columns:
    t = pd.to_datetime(df["time"])
    print("Time column parsed. First/last:", t.iloc[0], t.iloc[-1])
elif isinstance(df.index, pd.DatetimeIndex):
    t = df.index
    print("DatetimeIndex. First/last:", t[0], t[-1])
else:
    t = pd.to_timedelta(np.arange(len(df)) / fs, unit="s")
    print("No explicit time; generated seconds/timedelta")

duration_s = len(df) / fs
print("Duration seconds:", duration_s, "minutes:", duration_s/60)

for mod in ["biopsykit", "neurokit2", "scipy", "matplotlib"]:
    try:
        m = importlib.import_module(mod)
        print(f"Package {mod}: available, version={getattr(m, '__version__', 'unknown')}")
    except Exception as e:
        print(f"Package {mod}: not available ({e})")

# Inspect biopsykit ecg module if available
try:
    import biopsykit
    import biopsykit.signals.ecg as b_ecg
    print("biopsykit.signals.ecg members containing peak/r:")
    names = [n for n in dir(b_ecg) if "peak" in n.lower() or "r" == n.lower()[0:1] or "outlier" in n.lower()]
    print(names[:100])
except Exception as e:
    print("Could not inspect biopsykit.signals.ecg:", repr(e))