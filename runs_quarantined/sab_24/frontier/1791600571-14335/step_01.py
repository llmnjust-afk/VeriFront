#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import pickle

import pandas as pd
import numpy as np

print("Working directory:", os.getcwd())
print("Files in ecg_processing_data:", os.listdir("ecg_processing_data"))

sr_path = Path("ecg_processing_data/sampling_rate.txt")
fs = float(sr_path.read_text().strip())
print("Sampling rate:", fs)

pkl_path = Path("ecg_processing_data/ecg_data.pkl")
try:
    obj = pd.read_pickle(pkl_path)
    print("Loaded pickle with pandas. Type:", type(obj))
except Exception as e:
    print("pandas read_pickle failed:", repr(e))
    with open(pkl_path, "rb") as f:
        obj = pickle.load(f)
    print("Loaded pickle with pickle. Type:", type(obj))

if isinstance(obj, pd.DataFrame):
    df = obj
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

# Inspect optional package availability
for mod in ["biopsykit", "neurokit2", "scipy", "matplotlib"]:
    try:
        m = __import__(mod)
        print(f"Package {mod}: available, version={getattr(m, '__version__', 'unknown')}")
    except Exception as e:
        print(f"Package {mod}: not available ({e})")