import os
import json
from pathlib import Path
import pandas as pd
import numpy as np

train_path = "benchmark/datasets/dkpes/dkpes_train.csv"
test_path = "benchmark/datasets/dkpes/dkpes_test.csv"
train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

print("Train shape:", train.shape)
print("Test shape:", test.shape)
print("Columns:", list(train.columns))
print("\nTrain head:")
print(train.head().to_string())
print("\nTest head:")
print(test.head().to_string())

target = "Signal-inhibition"
print("\nTarget summary train:")
print(train[target].describe(percentiles=[.01,.05,.1,.2,.25,.3,.33,.4,.5,.6,.67,.7,.75,.8,.9,.95,.99]).to_string())
print("\nTarget summary test (for understanding only; predictions must be saved):")
print(test[target].describe(percentiles=[.01,.05,.1,.2,.25,.3,.33,.4,.5,.6,.67,.7,.75,.8,.9,.95,.99]).to_string())

print("\nMissing values train nonzero:")
miss = train.isna().sum()
print(miss[miss>0].to_string() if (miss>0).any() else "None")
print("\nMissing values test nonzero:")
miss = test.isna().sum()
print(miss[miss>0].to_string() if (miss>0).any() else "None")

print("\nDtypes:")
print(train.dtypes.to_string())

# Inspect categorical ShapeQuery levels and relationship with target.
print("\nShapeQuery summary:")
print("Train nunique:", train["ShapeQuery"].nunique(), "Test nunique:", test["ShapeQuery"].nunique())
print("Unseen in test vs train:", len(set(test["ShapeQuery"]) - set(train["ShapeQuery"])))
sq_stats = train.groupby("ShapeQuery")[target].agg(["count","mean","median","min","max"]).sort_values("mean", ascending=False)
print(sq_stats.head(15).to_string())
print("...")
print(sq_stats.tail(15).to_string())

# Basic correlations numeric
num_cols = train.select_dtypes(include=[np.number]).columns.tolist()
corr = train[num_cols].corr(numeric_only=True)[target].drop(target).sort_values(key=lambda s: s.abs(), ascending=False)
print("\nTop abs correlations with target:")
print(corr.head(20).to_string())

Path("work_info").mkdir(exist_ok=True)
with open("work_info/dkpes_paths.txt", "w") as f:
    f.write(train_path + "\n" + test_path + "\n")
print("\nSaved paths.")