#!/usr/bin/env python3
import os
import json
import pandas as pd
from pathlib import Path

print("Working directory:", os.getcwd())
print("Top directory listing:", os.listdir("."))

print("\nSearching for dkpes CSV files...")
matches = []
for root, dirs, files in os.walk("."):
    for fn in files:
        if "dkpes" in fn.lower() or root.lower().endswith("dkpes"):
            matches.append(os.path.join(root, fn))
for m in matches:
    print(m)

train_candidates = list(Path(".").rglob("dkpes_train.csv"))
test_candidates = list(Path(".").rglob("dkpes_test.csv"))
print("\ntrain candidates:", [str(p) for p in train_candidates])
print("test candidates:", [str(p) for p in test_candidates])

if not train_candidates or not test_candidates:
    print("\nNo direct dkpes_train/test found. Directory tree to depth 4:")
    for root, dirs, files in os.walk("."):
        depth = len(Path(root).parts)
        if depth <= 4:
            print(root, "dirs=", dirs[:10], "files=", files[:10])
    raise SystemExit("Could not find DKPES files")

train_path = train_candidates[0]
test_path = test_candidates[0]
print(f"\nUsing train: {train_path}")
print(f"Using test:  {test_path}")

summary = {}
for path in [train_path, test_path]:
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

    summary[str(path)] = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": {c: int(v) for c, v in df.isna().sum().items()},
    }
    if "Signal-inhibition" in df.columns:
        summary[str(path)]["signal_summary"] = df["Signal-inhibition"].describe().to_dict()
        summary[str(path)]["signal_quantiles"] = df["Signal-inhibition"].quantile([0, .1, .25, .5, .75, .9, .95, .99, 1]).to_dict()

summary["chosen_train_path"] = str(train_path)
summary["chosen_test_path"] = str(test_path)
with open("inspection_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nWrote inspection_summary.json")