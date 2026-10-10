#!/usr/bin/env python3
import os
import sys
import json
import importlib.util
from pathlib import Path

print("Working directory:", os.getcwd())
print("Files in biosignals:")
for p in sorted(Path("biosignals").glob("*")):
    print(" -", p, p.stat().st_size, "bytes")

for pkg in ["numpy", "pandas", "scipy", "neurokit2"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}: {'available' if spec else 'NOT available'}")

import pandas as pd
df = pd.read_csv("biosignals/bio_eventrelated_100hz.csv")
print("Loaded shape:", df.shape)
print("Columns:", list(df.columns))
print("Head:")
print(df.head().to_string())
print("Describe RSP:")
print(df["RSP"].describe().to_string())
print("NaNs per column:")
print(df.isna().sum().to_string())

# Persist a small metadata file for the next round
Path("pred_results").mkdir(exist_ok=True)
meta = {"shape": df.shape, "columns": list(df.columns), "sampling_rate": 100}
Path("pred_results/rrv_progress_meta.json").write_text(json.dumps(meta, indent=2))
print("Wrote pred_results/rrv_progress_meta.json")