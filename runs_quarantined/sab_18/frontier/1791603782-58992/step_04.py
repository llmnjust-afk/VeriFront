#!/usr/bin/env python3
import os
import pandas as pd

train_path = "benchmark/datasets/dili/train.csv"
test_path = "benchmark/datasets/dili/test.csv"
train = pd.read_csv(train_path)
test = pd.read_csv(test_path)
print("train shape:", train.shape)
print("test shape:", test.shape)
print("train columns:", list(train.columns))
print("test columns:", list(test.columns))
print("\ntrain head:")
print(train.head(10).to_string())
print("\ntrain tail:")
print(train.tail(10).to_string())
print("\ntest head:")
print(test.head(10).to_string())
print("\ntest tail:")
print(test.tail(10).to_string())
print("\nvDILIConcern counts:")
print(train["vDILIConcern"].value_counts(dropna=False).to_string())
if "vDILIConcern" in test.columns:
    print("\ntest vDILIConcern counts:")
    print(test["vDILIConcern"].value_counts(dropna=False).to_string())
print("\nIndex/unnamed min max:")
first_col = train.columns[0]
print(first_col, train[first_col].min(), train[first_col].max(), train[first_col].head().tolist(), train[first_col].tail().tolist())
print("\nRows at split boundaries (0-based iloc around 172,173,432,433,659,660):")
for i in [0, 172, 173, 432, 433, 659, 660, 922]:
    if 0 <= i < len(train):
        print("iloc", i, train.iloc[i][[first_col, "Compound Name", "vDILIConcern", "standardised_smiles"]].to_dict())