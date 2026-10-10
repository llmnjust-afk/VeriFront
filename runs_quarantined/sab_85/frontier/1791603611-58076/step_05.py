import os
import json
from pathlib import Path
import pandas as pd
import numpy as np

data_path = Path("benchmark/datasets/saliva_data/data.pkl")
print(f"Loading data from {data_path} (exists={data_path.exists()}, size={data_path.stat().st_size if data_path.exists() else 'NA'} bytes)")
df = pd.read_pickle(data_path)

print("Loaded type:", type(df))
print("Shape:", df.shape)
print("Index names:", df.index.names)
print("Columns:", list(df.columns))
print("Head:")
print(df.head(12))
print("\nInfo summary:")
print(df.reset_index().groupby(["condition", "subject"]).size().head(20))
print("Number condition-subject groups:", df.reset_index().groupby(["condition", "subject"]).ngroups)

# Normalize to a simple dataframe with columns condition, subject, sample, cortisol.
work = df.reset_index()
if "cortisol" not in work.columns:
    raise ValueError(f"Expected 'cortisol' column, found {work.columns.tolist()}")

features = {}
grouped = work.groupby(["condition", "subject"], sort=True)
for (condition, subject), g in grouped:
    g = g.sort_values("sample") if "sample" in g.columns else g.copy()
    values = pd.to_numeric(g["cortisol"], errors="coerce")
    valid = g.loc[values.notna()].copy()
    values = pd.to_numeric(valid["cortisol"], errors="coerce")
    if len(values) == 0:
        argmax = None
        mean = std = skew = kurt = None
    else:
        # BioPsyKit standard_features names argmax as argument/index of max value.
        # With sample in the index, this is the sample label at which cortisol is maximal.
        max_pos = values.to_numpy().argmax()
        if "sample" in valid.columns:
            argmax_val = valid.iloc[max_pos]["sample"]
            if isinstance(argmax_val, np.generic):
                argmax_val = argmax_val.item()
            argmax = argmax_val
        else:
            argmax = int(max_pos)
        mean = values.mean()
        std = values.std(ddof=1)
        skew = values.skew()
        kurt = values.kurt()
    features[str(subject)] = {
        "condition": str(condition),
        "argmax": None if argmax is None else (int(argmax) if isinstance(argmax, (int, np.integer)) else float(argmax) if isinstance(argmax, (float, np.floating)) else str(argmax)),
        "mean": None if pd.isna(mean) else float(mean),
        "std": None if pd.isna(std) else float(std),
        "skew": None if pd.isna(skew) else float(skew),
        "kurt": None if pd.isna(kurt) else float(kurt),
    }

out_dir = Path("pred_results")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "saliva_pred.json"
with out_path.open("w", encoding="utf-8") as f:
    json.dump(features, f, indent=2, sort_keys=True)

print(f"\nSaved {len(features)} subject feature dictionaries to {out_path}")
print("Output file size:", out_path.stat().st_size, "bytes")
print("First few entries:")
for i, (subject, vals) in enumerate(features.items()):
    print(subject, vals)
    if i >= 4:
        break
print("\nCondition counts in output:")
print(pd.Series([v["condition"] for v in features.values()]).value_counts().to_string())