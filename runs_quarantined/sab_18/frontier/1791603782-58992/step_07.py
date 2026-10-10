#!/usr/bin/env python3
import os
import pandas as pd

print("pred_results exists:", os.path.isdir("pred_results"))
print("files:", sorted(os.listdir("pred_results")))

for name in ["MCNC", "MCLCNC", "all"]:
    path = f"pred_results/{name}_RF.csv"
    print("\n", path, "exists:", os.path.exists(path))
    if os.path.exists(path):
        df = pd.read_csv(path)
        print("shape:", df.shape)
        print("columns:", list(df.columns))
        print("label counts:", df["label"].value_counts().to_dict())
        print("head:")
        print(df.head(8).to_string(index=False))
        print("valid labels only:", set(df["label"]).issubset({"DILI", "NoDILI"}))