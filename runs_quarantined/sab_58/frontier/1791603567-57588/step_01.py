#!/usr/bin/env python3
import os
import pandas as pd

print("Working directory:", os.getcwd())
for root, dirs, files in os.walk("nvc"):
    level = root.count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    for f in files[:20]:
        path = os.path.join(root, f)
        print(f"{indent}  {f} ({os.path.getsize(path)} bytes)")
    if len(files) > 20:
        print(f"{indent}  ... {len(files)-20} more files")

print("\nTop-level CSV previews/shapes:")
for path in [
    "nvc/ind_data_for_plot.csv",
    "nvc/valid_syllogisms.csv",
    "nvc/accuracies_data_for_plot.csv",
    "nvc/Ragni2016.csv",
]:
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            print("\n", path, df.shape)
            print(df.head().to_string())
            print("columns:", list(df.columns))
        except Exception as e:
            print("ERROR reading", path, e)

print("\nModel CSV previews:")
for sub in ["indiv_table", "prediction_errors"]:
    model_dir = f"nvc/scripts/{sub}/models"
    print("\nDirectory:", model_dir)
    if os.path.isdir(model_dir):
        for f in sorted(os.listdir(model_dir)):
            path = os.path.join(model_dir, f)
            try:
                df = pd.read_csv(path)
                print(f"\n{path} shape={df.shape} columns={list(df.columns)}")
                print(df.head().to_string())
            except Exception as e:
                print("ERROR", path, e)

print("\nRule file snippets:")
for sub in ["indiv_table", "prediction_errors", "nvc_prediction"]:
    rule_dir = f"nvc/scripts/{sub}/rules"
    print("\nDirectory:", rule_dir)
    if os.path.isdir(rule_dir):
        for f in sorted(os.listdir(rule_dir)):
            if f.endswith(".py") and f != "__init__.py":
                path = os.path.join(rule_dir, f)
                print(f"\n--- {path} ---")
                with open(path, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()
                print("".join(lines[:80]))