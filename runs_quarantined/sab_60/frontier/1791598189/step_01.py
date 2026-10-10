#!/usr/bin/env python3
import os
import pandas as pd

print("Working directory:", os.getcwd())
for root, dirs, files in os.walk("nvc"):
    level = root.count(os.sep) - "nvc".count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    for f in files[:20]:
        path = os.path.join(root, f)
        print(f"{indent}  {f} ({os.path.getsize(path)} bytes)")
    if len(files) > 20:
        print(f"{indent}  ... {len(files)-20} more files")

print("\nTop-level CSV previews:")
for fn in ["nvc/valid_syllogisms.csv", "nvc/accuracies_data_for_plot.csv", "nvc/ind_data_for_plot.csv", "nvc/Ragni2016.csv"]:
    if os.path.exists(fn):
        print("\n==", fn, "==")
        try:
            df = pd.read_csv(fn)
            print("shape", df.shape)
            print("columns", list(df.columns))
            print(df.head(8).to_string(index=False))
        except Exception as e:
            print("ERROR reading", e)

print("\nModel CSV previews:")
for sub in ["indiv_table/models", "prediction_errors/models"]:
    d = os.path.join("nvc/scripts", sub)
    if os.path.isdir(d):
        print("\n--", d, "--")
        for f in sorted(os.listdir(d)):
            if f.endswith(".csv"):
                path = os.path.join(d, f)
                try:
                    df = pd.read_csv(path)
                    print(f"\n{f}: shape {df.shape}, columns {list(df.columns)}")
                    print(df.head(5).to_string(index=False))
                except Exception as e:
                    print(f"{f}: ERROR {e}")

print("\nRule module snippets:")
for sub in ["indiv_table/rules", "prediction_errors/rules", "nvc_prediction/rules"]:
    d = os.path.join("nvc/scripts", sub)
    if os.path.isdir(d):
        print("\n--", d, "--")
        for f in sorted(os.listdir(d)):
            if f.endswith(".py") and f != "__init__.py":
                path = os.path.join(d, f)
                print(f"\n### {path}")
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        lines = fh.readlines()
                    print("".join(lines[:80]))
                except Exception as e:
                    print("ERROR", e)