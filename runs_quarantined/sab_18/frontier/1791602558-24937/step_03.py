#!/usr/bin/env python3
import os
import pandas as pd

base = "benchmark/datasets/dili"
train_path = os.path.join(base, "train.csv")
test_path = os.path.join(base, "test.csv")

for path in [train_path, test_path]:
    print("\n==", path, "==")
    df = pd.read_csv(path)
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print(df.head(10).to_string())
    print(df.tail(5).to_string())
    if "vDILIConcern" in df.columns:
        print("vDILIConcern counts:")
        print(df["vDILIConcern"].value_counts(dropna=False).to_string())
    print("missing smiles:", df["standardised_smiles"].isna().sum())

train = pd.read_csv(train_path)
print("\nSplit checks (0-based iloc ranges corresponding to 1-based task ranges):")
splits = {
    "MC": (0, 173),
    "LC": (173, 433),
    "NC": (433, 660),
    "sider": (660, 923),
}
for name, (a,b) in splits.items():
    sub = train.iloc[a:b]
    print(name, a, b, "n=", len(sub))
    print(sub["vDILIConcern"].value_counts(dropna=False).to_string())