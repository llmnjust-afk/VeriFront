#!/usr/bin/env python3
import os
import sys
import importlib.util
from pathlib import Path

print("Working directory:", os.getcwd())
data_path = Path("biosignals/bio_resting_5min_100hz.csv")
print("Data file exists:", data_path.exists(), data_path)

for pkg in ["pandas", "numpy", "scipy", "neurokit2"]:
    spec = importlib.util.find_spec(pkg)
    print(f"{pkg} available:", spec is not None)

if data_path.exists():
    import pandas as pd
    df = pd.read_csv(data_path)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print(df.head().to_string())
    print(df.describe().to_string())