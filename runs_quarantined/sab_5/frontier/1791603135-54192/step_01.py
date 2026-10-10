import os
import pandas as pd
import numpy as np

print("Working directory:", os.getcwd())
print("Files:", os.listdir("."))
print("dkpes files:", os.listdir("dkpes") if os.path.isdir("dkpes") else "missing")

train_path = "dkpes/dkpes_train.csv"
test_path = "dkpes/dkpes_test.csv"
train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

print("Train shape:", train.shape)
print("Test shape:", test.shape)
print("Train columns:", list(train.columns))
print("Test columns:", list(test.columns))
print("\nTrain head:")
print(train.head().to_string())
print("\nTest head:")
print(test.head().to_string())

print("\nSignal-inhibition summary:")
print(train["Signal-inhibition"].describe(percentiles=[.05,.1,.2,.25,.3,.4,.5,.6,.7,.75,.8,.9,.95]).to_string())
print("\nMissing values train:")
print(train.isna().sum().to_string())
print("\nMissing values test:")
print(test.isna().sum().to_string())

print("\nUnique ShapeQuery train/test counts:", train["ShapeQuery"].nunique(), test["ShapeQuery"].nunique())
print("Top ShapeQuery train:")
print(train["ShapeQuery"].value_counts().head(10).to_string())