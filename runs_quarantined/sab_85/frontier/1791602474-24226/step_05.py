#!/usr/bin/env python3
import os
import json
from pathlib import Path
import math
import pandas as pd
import numpy as np

DATA_CANDIDATES = [
    Path("saliva_data/data.pkl"),
    Path("benchmark/datasets/saliva_data/data.pkl"),
]
OUT_PATH = Path("pred_results/saliva_pred.json")

data_path = None
for p in DATA_CANDIDATES:
    if p.exists():
        data_path = p
        break
if data_path is None:
    raise FileNotFoundError(f"None of the candidate data files exist: {DATA_CANDIDATES}")

print(f"Loading data from {data_path} ...")
df = pd.read_pickle(data_path)
print("Loaded object:", type(df))
print("Shape:", getattr(df, "shape", None))
print("Index names:", df.index.names)
print("Columns:", list(df.columns))
print("Head:")
print(df.head(12))

if "cortisol" not in df.columns:
    raise ValueError(f"Expected column 'cortisol', got columns {list(df.columns)}")
for lvl in ["condition", "subject", "sample"]:
    if lvl not in df.index.names:
        raise ValueError(f"Expected index level {lvl!r}, got index names {df.index.names}")

# Sort by index for deterministic grouping/output.
df = df.sort_index()

def json_safe_value(x):
    """Convert pandas/numpy scalar to JSON-safe Python scalar; NaN/inf -> None."""
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        xf = float(x)
        return xf if math.isfinite(xf) else None
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if pd.isna(x):
        return None
    return x.item() if hasattr(x, "item") else x

def sample_label_from_idx(idx, names):
    if isinstance(idx, tuple):
        return idx[names.index("sample")]
    return idx

results = {}
feature_rows = []

# Compute BioPsyKit-like standard saliva features per subject:
# argmax, mean, std, skew, kurt. Pandas defaults use unbiased std (ddof=1),
# Fisher kurtosis, and adjusted skew/kurt, matching common standard feature behavior.
for (condition, subject), group in df.groupby(level=["condition", "subject"], sort=True):
    s = group["cortisol"].astype(float)
    argmax_idx = s.idxmax()
    argmax_sample = sample_label_from_idx(argmax_idx, s.index.names)
    feats = {
        "condition": str(condition),
        "argmax": json_safe_value(argmax_sample),
        "mean": json_safe_value(s.mean()),
        "std": json_safe_value(s.std()),
        "skew": json_safe_value(s.skew()),
        "kurt": json_safe_value(s.kurt()),
    }
    results[str(subject)] = feats
    row = {"condition": condition, "subject": subject, **feats}
    feature_rows.append(row)

print("\nNumber of subjects:", len(results))
print("Conditions and counts:")
cond_counts = {}
for subj, feats in results.items():
    cond_counts[feats["condition"]] = cond_counts.get(feats["condition"], 0) + 1
print(cond_counts)

features_df = pd.DataFrame(feature_rows).set_index(["condition", "subject"]).sort_index()
print("\nFeature preview:")
print(features_df.head(20))
print("\nFeature summary:")
print(features_df[["argmax", "mean", "std", "skew", "kurt"]].describe(include="all"))

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, sort_keys=True, allow_nan=False)

print(f"\nSaved JSON to {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
print("Sample saved entries:")
for k in sorted(results)[:5]:
    print(k, results[k])