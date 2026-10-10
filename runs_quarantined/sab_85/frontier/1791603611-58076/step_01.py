import os
import pickle
import json
import pandas as pd
import numpy as np

data_path = "saliva_data/data.pkl"
print(f"Checking for dataset at: {data_path}")
print("Exists:", os.path.exists(data_path))

df = pd.read_pickle(data_path)
print("Loaded object type:", type(df))
print("Shape:", df.shape)
print("Index names:", df.index.names)
print("Columns:", list(df.columns))
print("Head:")
print(df.head(10))
print("Index levels and counts:")
if isinstance(df.index, pd.MultiIndex):
    for name, level in zip(df.index.names, df.index.levels):
        print(name, len(level), list(level)[:10])
print("Describe cortisol:")
print(df["cortisol"].describe())
print("Missing cortisol values:", int(df["cortisol"].isna().sum()))