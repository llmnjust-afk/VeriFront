#!/usr/bin/env python3
import os
import sys
import importlib.util
import pandas as pd
import numpy as np

path = "benchmark/datasets/biosignals/bio_eventrelated_100hz.csv"
print("Working directory:", os.getcwd())
print("Using data path:", path, "exists:", os.path.exists(path))

df = pd.read_csv(path)
print("Loaded shape:", df.shape)
print("Columns:", list(df.columns))
print("Head:")
print(df.head().to_string(index=False))
print("Tail:")
print(df.tail().to_string(index=False))
print("NaN counts:")
print(df.isna().sum().to_string())

fs = 100
duration = len(df) / fs
print(f"Assumed sampling rate: {fs} Hz")
print(f"Duration: {duration:.2f} s ({duration/60:.2f} min)")

for pkg in ["neurokit2", "scipy", "numpy", "pandas"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}:", "available" if spec is not None else "NOT available")
    if spec is not None:
        mod = __import__(pkg)
        print(f"  version: {getattr(mod, '__version__', 'unknown')}")

rsp = pd.to_numeric(df["RSP"], errors="coerce").to_numpy()
print("RSP finite:", np.isfinite(rsp).sum(), "/", len(rsp))
print("RSP min/max/mean/std:", np.nanmin(rsp), np.nanmax(rsp), np.nanmean(rsp), np.nanstd(rsp))
print("First 20 RSP:", np.array2string(rsp[:20], precision=6, separator=", "))