import json
from pathlib import Path
import pandas as pd
import numpy as np

data_path = Path("benchmark/datasets/saliva_data/data.pkl")
df = pd.read_pickle(data_path)
work = df.reset_index()
print("Dtypes after reset_index:")
print(work.dtypes)
print("\nUnique sample values and Python types:")
for x in sorted(work["sample"].unique(), key=lambda v: str(v)):
    print(repr(x), type(x))

print("\nChecking whether biopsykit is available and its standard_features output:")
try:
    import biopsykit as bp
    import biopsykit.saliva as saliva
    print("biopsykit imported:", getattr(bp, "__version__", "unknown version"))
    print("saliva.standard_features:", saliva.standard_features)
    try:
        bk_features = saliva.standard_features(df)
        print("BioPsyKit output type:", type(bk_features))
        print("BioPsyKit output:")
        print(bk_features.head(30) if hasattr(bk_features, "head") else bk_features)
    except Exception as e:
        print("Calling biopsykit.saliva.standard_features failed:", repr(e))
except Exception as e:
    print("biopsykit not available or import failed:", repr(e))

# Recompute output, coercing numeric-looking sample labels to ints for argmax.
features = {}
for (condition, subject), g in work.groupby(["condition", "subject"], sort=True):
    g = g.sort_values("sample")
    vals = pd.to_numeric(g["cortisol"], errors="coerce")
    valid = g.loc[vals.notna()].copy()
    vals = pd.to_numeric(valid["cortisol"], errors="coerce")
    if vals.empty:
        feat = {"condition": str(condition), "argmax": None, "mean": None, "std": None, "skew": None, "kurt": None}
    else:
        max_pos = int(vals.to_numpy().argmax())
        argmax = valid.iloc[max_pos]["sample"]
        # Convert numpy scalars and numeric strings cleanly for JSON.
        if isinstance(argmax, np.generic):
            argmax = argmax.item()
        if isinstance(argmax, str):
            try:
                as_float = float(argmax)
                argmax = int(as_float) if as_float.is_integer() else as_float
            except ValueError:
                pass
        feat = {
            "condition": str(condition),
            "argmax": argmax,
            "mean": float(vals.mean()),
            "std": float(vals.std(ddof=1)),
            "skew": float(vals.skew()),
            "kurt": float(vals.kurt()),
        }
    features[str(subject)] = feat

out_path = Path("pred_results/saliva_pred.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8") as f:
    json.dump(features, f, indent=2, sort_keys=True)

print(f"\nRe-saved cleaned output to {out_path}")
print("First five JSON entries:")
for i, (k, v) in enumerate(features.items()):
    print(k, v)
    if i >= 4:
        break
print("argmax Python types in output:", sorted({type(v["argmax"]).__name__ for v in features.values()}))
print("File size:", out_path.stat().st_size, "bytes")