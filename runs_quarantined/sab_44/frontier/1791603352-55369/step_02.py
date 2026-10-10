#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
import numpy as np
import inspect

print("CWD:", os.getcwd())
print("Recursive files (max 100):")
for i, p in enumerate(Path(".").rglob("*")):
    if i >= 100:
        print("... truncated")
        break
    print(p, "dir" if p.is_dir() else f"file {p.stat().st_size} bytes")

# Find sleep_data.pkl
candidates = list(Path(".").rglob("sleep_data.pkl"))
print("sleep_data.pkl candidates:", candidates)

# Inspect BioPsyKit pipeline signature/source head
from biopsykit.sleep import sleep_processing_pipeline
fn = sleep_processing_pipeline.predict_pipeline_acceleration
print("predict_pipeline_acceleration:", fn)
print("signature:", inspect.signature(fn))
try:
    src = inspect.getsource(fn)
    print("source first 4000 chars:\n", src[:4000])
except Exception as e:
    print("Could not get source:", repr(e))

if candidates:
    p = candidates[0]
    print("Loading", p)
    df = pd.read_pickle(p)
    print("Loaded type:", type(df))
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("Dtypes:\n", df.dtypes)
    print("Head:\n", df.head().to_string())
    print("Tail:\n", df.tail().to_string())
    if "time" in df.columns:
        t = pd.to_datetime(df["time"])
    else:
        t = pd.to_datetime(df.index)
    print("Time first/last:", t.iloc[0], t.iloc[-1])
    print("Duration:", t.iloc[-1] - t.iloc[0])
    dt = t.diff().dropna().dt.total_seconds()
    print("dt describe:\n", dt.describe(percentiles=[.01,.05,.5,.95,.99]).to_string())
    print("Approx fs median:", 1.0 / dt.median())