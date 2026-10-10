#!/usr/bin/env python3
import os
import pickle
import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np

print("CWD:", os.getcwd())
print("Files:", list(Path(".").glob("*")))
print("Data exists:", Path("sleep_imu_data/sleep_data.pkl").exists())

# Check BioPsyKit availability and relevant API
try:
    import biopsykit
    print("biopsykit version:", getattr(biopsykit, "__version__", "unknown"))
    try:
        from biopsykit.sleep import sleep_processing_pipeline
        print("Imported biopsykit.sleep.sleep_processing_pipeline")
        print("Available attrs:", [a for a in dir(sleep_processing_pipeline) if "predict" in a.lower() or "pipeline" in a.lower()][:50])
    except Exception as e:
        print("Could not import sleep_processing_pipeline:", repr(e))
except Exception as e:
    print("biopsykit import failed:", repr(e))

# Load data
p = Path("sleep_imu_data/sleep_data.pkl")
obj = pd.read_pickle(p)
print("Loaded type:", type(obj))
if isinstance(obj, pd.DataFrame):
    df = obj
else:
    print("Object repr:", repr(obj)[:1000])
    df = pd.DataFrame(obj)

print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("Dtypes:", df.dtypes)
print("Head:")
print(df.head())
print("Tail:")
print(df.tail())

# Basic time information
if "time" in df.columns:
    t = pd.to_datetime(df["time"])
else:
    t = pd.to_datetime(df.index)
print("Time first/last:", t.iloc[0], t.iloc[-1])
print("Duration:", t.iloc[-1] - t.iloc[0])
dt = t.diff().dropna().dt.total_seconds()
print("dt describe:", dt.describe(percentiles=[.01,.05,.5,.95,.99]).to_string())
print("Approx fs median:", 1.0 / dt.median())

# Sensor statistics and coarse activity
cols = [c for c in df.columns if c != "time"]
print("Sensor describe:")
print(df[cols].describe().to_string())

gyr_cols = [c for c in cols if c.startswith("gyr")]
acc_cols = [c for c in cols if c.startswith("acc")]
if gyr_cols:
    gyr_mag = np.sqrt((df[gyr_cols].astype(float) ** 2).sum(axis=1))
    print("gyr_mag quantiles:", gyr_mag.quantile([0, .01, .05, .1, .25, .5, .75, .9, .95, .99, 1]).to_string())
if acc_cols:
    acc = df[acc_cols].astype(float)
    acc_mag = np.sqrt((acc ** 2).sum(axis=1))
    print("acc_mag quantiles:", acc_mag.quantile([0, .01, .05, .1, .25, .5, .75, .9, .95, .99, 1]).to_string())