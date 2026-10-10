#!/usr/bin/env python3
import os
import pandas as pd

base = "benchmark/datasets/nvc"

# Compact inspection focused on schemas/unique values
for rel in ["Ragni2016.csv", "ind_data_for_plot.csv", "accuracies_data_for_plot.csv", "valid_syllogisms.csv"]:
    path=os.path.join(base,rel)
    df=pd.read_csv(path)
    print("\n==", rel, "==")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    for col in df.columns:
        vals = df[col].dropna().unique()
        print(f"  {col}: nunique={len(vals)} sample={list(vals[:12])}")
    print("head:")
    print(df.head(5).to_string(index=False))

# show all rows of small ind_data
print("\nind_data_for_plot full:")
print(pd.read_csv(os.path.join(base,"ind_data_for_plot.csv")).to_string(index=False))

# Model CSV complete content
for sub in ["scripts/indiv_table/models", "scripts/prediction_errors/models"]:
    print("\n###", sub)
    for fn in sorted(os.listdir(os.path.join(base, sub))):
        if not fn.endswith(".csv"): continue
        df=pd.read_csv(os.path.join(base,sub,fn))
        print("\n--", fn, "shape", df.shape)
        print(df.to_string(index=False))

# Rule function names and full text
for sub in ["scripts/indiv_table/rules", "scripts/prediction_errors/rules", "scripts/nvc_prediction/rules"]:
    print("\n### RULES", sub)
    for fn in sorted(os.listdir(os.path.join(base,sub))):
        if fn.endswith(".py") and fn != "__init__.py":
            path=os.path.join(base,sub,fn)
            print("\n--", fn)
            with open(path, encoding="utf-8") as f:
                print(f.read())