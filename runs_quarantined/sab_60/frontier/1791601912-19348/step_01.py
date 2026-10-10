#!/usr/bin/env python3
import os
import pandas as pd

print("Working directory:", os.getcwd())
print("Top-level entries:", sorted(os.listdir(".")))

base = "nvc"
print("nvc exists:", os.path.isdir(base))
for root, dirs, files in os.walk(base):
    level = root.count(os.sep) - base.count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    for f in sorted(files)[:20]:
        path = os.path.join(root, f)
        print(f"{indent}  {f} ({os.path.getsize(path)} bytes)")
    if level >= 3:
        dirs[:] = []

# Inspect key CSVs
for path in [
    "nvc/valid_syllogisms.csv",
    "nvc/accuracies_data_for_plot.csv",
    "nvc/ind_data_for_plot.csv",
    "nvc/Ragni2016.csv",
    "nvc/scripts/indiv_table/models/PSYCOP.csv",
    "nvc/scripts/prediction_errors/models/PSYCOP.csv",
]:
    print("\n---", path, "---")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            print("shape:", df.shape)
            print("columns:", list(df.columns))
            print(df.head(10).to_string(index=False))
        except Exception as e:
            print("Could not read:", repr(e))
    else:
        print("missing")

# Inspect rule scripts
for path in [
    "nvc/scripts/indiv_table/rules/atmosphere.py",
    "nvc/scripts/indiv_table/rules/figural.py",
    "nvc/scripts/indiv_table/rules/negativity.py",
    "nvc/scripts/prediction_errors/rules/atmosphere.py",
    "nvc/scripts/nvc_prediction/rules/atmosphere.py",
]:
    print("\n---", path, "---")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            print(f.read()[:4000])
    else:
        print("missing")