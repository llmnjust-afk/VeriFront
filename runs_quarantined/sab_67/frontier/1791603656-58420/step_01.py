import os
import numpy as np
import pandas as pd
from pathlib import Path

base = Path("CogSci_pattern_high_sim_data")
print("Working directory:", Path.cwd())
print("Dataset exists:", base.exists())
print("Files:")
for p in sorted(base.iterdir()):
    print(" -", p.name, p.stat().st_size, "bytes")

for npy in sorted(base.glob("*.npy")):
    arr = np.load(npy, allow_pickle=True)
    print("\nNPY:", npy.name)
    print(" type:", type(arr))
    print(" dtype:", getattr(arr, "dtype", None), " shape:", getattr(arr, "shape", None))
    if isinstance(arr, np.ndarray):
        print(" ndim:", arr.ndim)
        if arr.dtype == object:
            print(" object contents preview:")
            flat = arr.ravel()
            for i, x in enumerate(flat[:5]):
                print("  item", i, "type", type(x), "repr", repr(x)[:500])
        else:
            print(" min/max/sum:", np.nanmin(arr), np.nanmax(arr), np.nansum(arr))
            print(" first values:", arr.ravel()[:20])

print("\nCSV previews and summaries:")
for csv in sorted(base.glob("*.csv")):
    df = pd.read_csv(csv)
    print("\nCSV:", csv.name, "shape:", df.shape, "columns:", list(df.columns))
    print(df.head(10).to_string(index=False))
    print("unique syllogisms:", df["Syllogism"].nunique() if "Syllogism" in df else None)
    if "Prediction" in df:
        tokens = sorted(set(tok for s in df["Prediction"].fillna("").astype(str) for tok in s.split(";") if tok))
        print("unique prediction tokens:", len(tokens), tokens)