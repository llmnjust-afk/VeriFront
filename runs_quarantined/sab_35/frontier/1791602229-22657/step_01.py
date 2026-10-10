#!/usr/bin/env python3
import os
import sys
import importlib.util
import pandas as pd
import numpy as np

print("Working directory:", os.getcwd())
print("Files in biosignals:", os.listdir("biosignals") if os.path.isdir("biosignals") else "missing")

path = "biosignals/bio_eventrelated_100hz.csv"
df = pd.read_csv(path)
print("Loaded:", path)
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("Head:")
print(df.head().to_string(index=False))
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
        try:
            mod = __import__(pkg)
            print(f"  version: {getattr(mod, '__version__', 'unknown')}")
        except Exception as e:
            print("  import error:", repr(e))

rsp = pd.to_numeric(df["RSP"], errors="coerce").to_numpy()
print("RSP finite:", np.isfinite(rsp).sum(), "/", len(rsp))
print("RSP min/max/mean/std:", np.nanmin(rsp), np.nanmax(rsp), np.nanmean(rsp), np.nanstd(rsp))