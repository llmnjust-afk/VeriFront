#!/usr/bin/env python3
import os
import sys
import importlib.util
from pathlib import Path

print("Working directory:", os.getcwd())
print("Python:", sys.version)

data_path = Path("biosignals/bio_resting_5min_100hz.csv")
print("Data exists:", data_path.exists(), "path:", data_path)
if data_path.exists():
    print("Size bytes:", data_path.stat().st_size)
    with open(data_path, "r", encoding="utf-8") as f:
        for i in range(5):
            print(f"line {i+1}:", f.readline().rstrip())

for pkg in ["numpy", "pandas", "scipy", "neurokit2"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}: {'available' if spec is not None else 'NOT available'}")
    if spec is not None:
        try:
            mod = importlib.import_module(pkg)
            print(f"  version: {getattr(mod, '__version__', 'unknown')}")
        except Exception as e:
            print(f"  import error: {e}")

# Basic dataset shape/stat summary
try:
    import pandas as pd
    df = pd.read_csv(data_path)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print("Head:")
    print(df.head().to_string())
    print("Describe:")
    print(df.describe().to_string())
except Exception as e:
    print("Could not read/summarize dataset:", repr(e))