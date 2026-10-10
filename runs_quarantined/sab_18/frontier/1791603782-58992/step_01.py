#!/usr/bin/env python3
import os
import sys
import importlib.util
import pandas as pd

print("CWD:", os.getcwd())
print("Files:", os.listdir("."))
print("dili files:", os.listdir("dili") if os.path.isdir("dili") else "NO dili dir")

for pkg in ["rdkit", "sklearn", "numpy", "pandas"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}: {'FOUND' if spec else 'MISSING'}")

train_path = "dili/train.csv"
test_path = "dili/test.csv"
train = pd.read_csv(train_path)
test = pd.read_csv(test_path)
print("train shape:", train.shape)
print("test shape:", test.shape)
print("train columns:", list(train.columns))
print("test columns:", list(test.columns))
print("train head:")
print(train.head().to_string())
print("test head:")
print(test.head().to_string())
print("vDILIConcern counts:")
print(train["vDILIConcern"].value_counts(dropna=False).to_string())
print("train index/minmax first unnamed if present:")
print(train.iloc[[0, -1]].to_string())
print("test columns counts and possible labels:")
for col in test.columns:
    if test[col].nunique(dropna=False) < 10:
        print(col, test[col].value_counts(dropna=False).to_dict())