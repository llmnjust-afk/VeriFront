#!/usr/bin/env python3
import os
import json
import pandas as pd

print("Working directory:", os.getcwd())
print("Directory listing:", os.listdir("."))

for path in ["dkpes/dkpes_train.csv", "dkpes/dkpes_test.csv"]:
    print("\n--- Inspecting", path, "---")
    df = pd.read_csv(path)
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print("head:")
    print(df.head().to_string())
    print("dtypes:")
    print(df.dtypes.to_string())
    print("missing values:")
    print(df.isna().sum().to_string())
    if "Signal-inhibition" in df.columns:
        print("Signal-inhibition summary:")
        print(df["Signal-inhibition"].describe().to_string())
        print("quantiles:")
        print(df["Signal-inhibition"].quantile([0, .1, .25, .5, .75, .9, .95, .99, 1]).to_string())

# Save an inspection summary for next round
summary = {}
for path in ["dkpes/dkpes_train.csv", "dkpes/dkpes_test.csv"]:
    df = pd.read_csv(path)
    summary[path] = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": {c: int(v) for c, v in df.isna().sum().items()},
    }
    if "Signal-inhibition" in df.columns:
        summary[path]["signal_summary"] = df["Signal-inhibition"].describe().to_dict()
        summary[path]["signal_quantiles"] = df["Signal-inhibition"].quantile([0, .1, .25, .5, .75, .9, .95, .99, 1]).to_dict()
with open("inspection_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nWrote inspection_summary.json")