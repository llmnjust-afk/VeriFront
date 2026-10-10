#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import os

root = Path("benchmark/datasets/nvc")
print("root exists", root.exists())

for fname in ["Ragni2016.csv","valid_syllogisms.csv","ind_data_for_plot.csv","accuracies_data_for_plot.csv"]:
    print("\n===", fname, "===")
    df = pd.read_csv(root/fname)
    print("shape", df.shape)
    print("cols", list(df.columns))
    print(df.head(12).to_string(index=False))
    print("dtypes", df.dtypes.to_dict())

for sub in ["indiv_table/models", "prediction_errors/models"]:
    d = root/"scripts"/sub
    print("\n=== Models in", sub, "===")
    for f in sorted(d.glob("*.csv")):
        df=pd.read_csv(f)
        print("\n---", f.name, "shape", df.shape, "cols", list(df.columns))
        print(df.head(12).to_string(index=False))

for sub in ["indiv_table/rules", "prediction_errors/rules", "nvc_prediction/rules"]:
    d=root/"scripts"/sub
    print("\n=== Rules in", sub, "===")
    for f in sorted(d.glob("*.py")):
        print("\n---", f.name, "---")
        print("\n".join(f.read_text().splitlines()[:120]))