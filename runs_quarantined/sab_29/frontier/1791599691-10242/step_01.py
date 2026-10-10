#!/usr/bin/env python3
import os
import sys
import json
import numpy as np
import pandas as pd

path = "biosignals/bio_eventrelated_100hz.csv"
print("Exists:", os.path.exists(path))
df = pd.read_csv(path)
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("Head:")
print(df.head().to_string())
print("Tail:")
print(df.tail().to_string())
print("Describe:")
print(df.describe().to_string())

# Inspect Photosensor values and transitions
ph = df["Photosensor"].to_numpy()
vals, counts = np.unique(ph, return_counts=True)
print("Unique Photosensor count:", len(vals))
print("First/last unique values:", vals[:20], vals[-20:])
print("Unique values with counts (up to 50):")
for v, c in zip(vals[:50], counts[:50]):
    print(repr(v), c)

# Find transitions of photosensor after rounding
thr_candidates = [0.5, 1, 2, 2.5, 3, 4]
for thr in thr_candidates:
    binary = ph > thr
    changes = np.where(np.diff(binary.astype(int)) != 0)[0] + 1
    print(f"\nThreshold {thr}: n_changes={len(changes)}")
    print("First 30 changes indices:", changes[:30].tolist())
    if len(changes):
        print("First 30 change times s:", (changes[:30] / 100).round(3).tolist())
        print("States around first changes:", [(int(i), float(ph[i-2]) if i>=2 else None, float(ph[i-1]), float(ph[i]), float(ph[min(i+1,len(ph)-1)])) for i in changes[:10]])

# Try import neurokit2
try:
    import neurokit2 as nk
    print("\nNeuroKit2 version:", getattr(nk, "__version__", "unknown"))
except Exception as e:
    print("\nNeuroKit2 import failed:", repr(e))