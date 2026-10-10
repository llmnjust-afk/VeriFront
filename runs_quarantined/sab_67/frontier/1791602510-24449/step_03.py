import os
import numpy as np
import pandas as pd

base = "benchmark/datasets/CogSci_pattern_high_sim_data"
print("Using base:", os.path.abspath(base))
print("Files:", sorted(os.listdir(base)))

# Inspect CSVs and NPYs enough to infer representation
csv_files = sorted([f for f in os.listdir(base) if f.endswith(".csv")])
all_syll = None
all_preds = set()
for fn in csv_files:
    df = pd.read_csv(os.path.join(base, fn))
    print("\nCSV", fn, "shape", df.shape)
    print(df.head(5).to_string(index=False))
    print("tail:")
    print(df.tail(5).to_string(index=False))
    print("unique syllogisms", df["Syllogism"].nunique(), "missing predictions", df["Prediction"].isna().sum())
    if all_syll is None:
        all_syll = list(df["Syllogism"])
    else:
        print("same syll order as first:", all_syll == list(df["Syllogism"]))
    for pred in df["Prediction"].fillna("").astype(str):
        for token in pred.split(";"):
            if token:
                all_preds.add(token)

print("\nAll prediction tokens:", sorted(all_preds), "count", len(all_preds))
print("Syllogism count:", len(all_syll), "first/last:", all_syll[:10], all_syll[-10:])

for fn in sorted([f for f in os.listdir(base) if f.endswith(".npy")]):
    arr = np.load(os.path.join(base, fn), allow_pickle=True)
    print("\nNPY", fn, "dtype", arr.dtype, "shape", arr.shape, "ndim", arr.ndim)
    try:
        print("min max sum mean:", np.nanmin(arr), np.nanmax(arr), np.nansum(arr), np.nanmean(arr))
    except Exception as e:
        print("numeric summary failed:", repr(e))
    flat = arr.ravel()
    print("first values:", flat[:30])
    if arr.ndim >= 2:
        print("first row:", arr[0, :min(arr.shape[1], 30)])
        print("last row:", arr[-1, :min(arr.shape[1], 30)])