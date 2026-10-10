#!/usr/bin/env python3
import os, glob, textwrap, importlib.util, sys, json
import pandas as pd

BASE = "benchmark/datasets/nvc"
print("BASE exists:", os.path.exists(BASE))

print("\nTop-level CSV previews:")
for fn in ["valid_syllogisms.csv", "accuracies_data_for_plot.csv", "ind_data_for_plot.csv", "Ragni2016.csv"]:
    path = os.path.join(BASE, fn)
    print("\n==", path, "==")
    df = pd.read_csv(path)
    print("shape", df.shape)
    print("columns", list(df.columns))
    print(df.head(10).to_string(index=False))
    print("dtypes", df.dtypes.to_dict())

print("\nModel CSV previews:")
for sub in ["indiv_table/models", "prediction_errors/models"]:
    d = os.path.join(BASE, "scripts", sub)
    print("\n--", d, "--")
    for f in sorted(os.listdir(d)):
        if f.endswith(".csv"):
            path = os.path.join(d, f)
            df = pd.read_csv(path)
            print(f"\n{f}: shape {df.shape}, columns {list(df.columns)}")
            print(df.head(10).to_string(index=False))
            print("unique counts:", {c: df[c].nunique(dropna=False) for c in df.columns[:8]})

print("\nRule module full-ish snippets:")
for sub in ["indiv_table/rules", "prediction_errors/rules", "nvc_prediction/rules"]:
    d = os.path.join(BASE, "scripts", sub)
    print("\n--", d, "--")
    for f in sorted(os.listdir(d)):
        if f.endswith(".py") and f != "__init__.py":
            path = os.path.join(d, f)
            print(f"\n### {path}")
            with open(path, "r", encoding="utf-8") as fh:
                txt = fh.read()
            print(txt[:5000])
            if len(txt) > 5000:
                print("...TRUNCATED...", len(txt), "chars")

print("\nMaybe README/scripts:")
for path in glob.glob(os.path.join(BASE, "scripts", "**", "*.py"), recursive=True):
    print(path)