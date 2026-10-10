#!/usr/bin/env python3
import os
import sys
import importlib.util
import pandas as pd

print("Working directory:", os.getcwd())
print("Python:", sys.version)

for pkg in ["pandas", "numpy", "sklearn", "rdkit"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}: {'FOUND' if spec else 'NOT FOUND'}")

for path in ["dili/train.csv", "dili/test.csv"]:
    print("\n===", path, "===")
    if os.path.exists(path):
        df = pd.read_csv(path)
        print("shape:", df.shape)
        print("columns:", list(df.columns))
        print(df.head().to_string())
        if "vDILIConcern" in df.columns:
            print("vDILIConcern counts:")
            print(df["vDILIConcern"].value_counts(dropna=False).to_string())
        if "standardised_smiles" in df.columns:
            print("missing smiles:", df["standardised_smiles"].isna().sum())
    else:
        print("MISSING")