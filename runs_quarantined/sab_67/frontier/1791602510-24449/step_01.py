import os
import numpy as np
import pandas as pd

base = "CogSci_pattern_high_sim_data"
print("Working dir:", os.getcwd())
print("Files:", sorted(os.listdir(base)))

# Inspect CSVs
for fn in sorted([f for f in os.listdir(base) if f.endswith(".csv")]):
    path = os.path.join(base, fn)
    df = pd.read_csv(path)
    print("\nCSV", fn, "shape", df.shape)
    print(df.head().to_string(index=False))
    print("tail:")
    print(df.tail(3).to_string(index=False))
    print("unique syllogisms", df["Syllogism"].nunique(), "missing predictions", df["Prediction"].isna().sum())

# Inspect npy files
for fn in sorted([f for f in os.listdir(base) if f.endswith(".npy")]):
    path = os.path.join(base, fn)
    arr = np.load(path, allow_pickle=True)
    print("\nNPY", fn, "type", type(arr), "dtype", getattr(arr, "dtype", None), "shape", getattr(arr, "shape", None))
    if isinstance(arr, np.ndarray):
        print("ndim", arr.ndim, "min/max/sum if numeric:")
        try:
            print(float(np.nanmin(arr)), float(np.nanmax(arr)), float(np.nansum(arr)))
        except Exception as e:
            print("numeric summary failed:", repr(e))
        print("repr sample:", repr(arr if arr.size <= 20 else arr.ravel()[:20]))