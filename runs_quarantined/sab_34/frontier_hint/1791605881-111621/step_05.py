#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

candidates = [
    Path("benchmark/datasets/biosignals/bio_resting_5min_100hz.csv"),
    Path("/data/lab/VeriFront/runs/sab_34/frontier/1791599745-10798/biosignals/bio_resting_5min_100hz.csv"),
]
print("Working directory:", os.getcwd())
for path in candidates:
    print("\nCandidate:", path)
    print(" exists:", path.exists())
    if path.exists():
        df = pd.read_csv(path)
        print(" shape:", df.shape)
        print(" columns:", list(df.columns))
        print(" head:")
        print(df.head().to_string())
        print(" describe ECG:")
        print(df["ECG"].describe().to_string())