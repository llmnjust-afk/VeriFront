#!/usr/bin/env python3
import os
import pandas as pd

base = "benchmark/datasets/nvc"
print("Using base:", base)

for path in [
    f"{base}/ind_data_for_plot.csv",
    f"{base}/valid_syllogisms.csv",
    f"{base}/accuracies_data_for_plot.csv",
    f"{base}/Ragni2016.csv",
]:
    print("\n==", path, "==")
    df = pd.read_csv(path)
    print("shape", df.shape)
    print("columns", list(df.columns))
    print(df.head(10).to_string(index=False))
    print("dtypes", df.dtypes.to_dict())

for sub in ["indiv_table", "prediction_errors"]:
    model_dir = f"{base}/scripts/{sub}/models"
    print("\n\nMODEL DIR", model_dir)
    for f in sorted(os.listdir(model_dir)):
        path = os.path.join(model_dir, f)
        df = pd.read_csv(path)
        print("\n==", path, "==")
        print("shape", df.shape)
        print("columns", list(df.columns))
        print(df.head(12).to_string(index=False))

for sub in ["indiv_table", "prediction_errors", "nvc_prediction"]:
    rule_dir = f"{base}/scripts/{sub}/rules"
    print("\n\nRULE DIR", rule_dir)
    for f in sorted(os.listdir(rule_dir)):
        if f.endswith(".py") and f != "__init__.py":
            path = os.path.join(rule_dir, f)
            print("\n---", path, "---")
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            print("".join(lines[:120]))