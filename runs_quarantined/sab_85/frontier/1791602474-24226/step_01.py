#!/usr/bin/env python3
import os
import json
import pickle
import pandas as pd

DATA_PATH = "saliva_data/data.pkl"
OUT_PATH = "pred_results/saliva_pred.json"

print(f"Loading data from {DATA_PATH!r} ...")
df = pd.read_pickle(DATA_PATH)

print("DataFrame type:", type(df))
print("Shape:", df.shape)
print("Index names:", df.index.names)
print("Columns:", list(df.columns))
print("Head:")
print(df.head(10))

print("\nIndex level values:")
for name in df.index.names:
    vals = df.index.get_level_values(name).unique().tolist()
    print(f"  {name}: n={len(vals)}, first={vals[:10]}")

# Compute one preliminary table to verify grouping and statistics.
def compute_group_features(g):
    s = g["cortisol"].astype(float)
    # argmax as the sample index label at which cortisol is maximal
    idxmax = s.idxmax()
    if isinstance(idxmax, tuple) and "sample" in s.index.names:
        argmax = idxmax[s.index.names.index("sample")]
    else:
        argmax = idxmax
    return pd.Series({
        "argmax": argmax,
        "mean": s.mean(),
        "std": s.std(),
        "skew": s.skew(),
        "kurt": s.kurt(),
    })

features = df.groupby(level=["condition", "subject"], sort=True).apply(compute_group_features)
print("\nComputed feature table preview:")
print(features.head(20))
print("\nFeature table shape:", features.shape)

# Build and save dictionary of dictionaries with subject as top-level key.
result = {}
for (condition, subject), row in features.iterrows():
    result[str(subject)] = {
        "condition": str(condition),
        "argmax": int(row["argmax"]) if pd.notna(row["argmax"]) and float(row["argmax"]).is_integer() else float(row["argmax"]),
        "mean": float(row["mean"]),
        "std": float(row["std"]),
        "skew": float(row["skew"]),
        "kurt": float(row["kurt"]),
    }

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, sort_keys=True)

print(f"\nSaved {len(result)} subject feature dictionaries to {OUT_PATH!r}")
print("First few JSON entries:")
for i, (k, v) in enumerate(result.items()):
    if i >= 5:
        break
    print(k, v)