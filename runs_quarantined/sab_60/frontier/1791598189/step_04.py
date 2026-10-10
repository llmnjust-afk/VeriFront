#!/usr/bin/env python3
import os
import pandas as pd

BASE = "benchmark/datasets/nvc"

# Inspect compact metadata needed to reconstruct/verify required accuracies.csv
acc = pd.read_csv(os.path.join(BASE, "accuracies_data_for_plot.csv"))
print("accuracies_data_for_plot shape:", acc.shape)
print("columns:", list(acc.columns))
print("models:", sorted(acc["model"].unique()))
print("nvc rules:", sorted(acc["nvc"].unique()))
print("tasks:", acc["task"].nunique(), sorted(acc["task"].unique())[:10], "...", sorted(acc["task"].unique())[-10:])
print("rows per model-rule (first 20):")
print(acc.groupby(["model","nvc"]).size().head(20).to_string())
print("hit_model/hit_nvc/improvement describe:")
print(acc[["hit_model","hit_nvc","improvement"]].describe().to_string())
print("sample rows:")
print(acc.head(25).to_string(index=False))

# Inspect model files compactly.
for sub in ["indiv_table/models", "prediction_errors/models"]:
    d = os.path.join(BASE, "scripts", sub)
    print("\nMODEL DIR", sub)
    for f in sorted(os.listdir(d)):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(d, f))
            print(f"{f}: shape={df.shape}, cols={list(df.columns)}")
            print(df.head(3).to_string(index=False))

# Inspect rule files compactly: function/class names and first 120 lines total enough.
for sub in ["indiv_table/rules", "prediction_errors/rules", "nvc_prediction/rules"]:
    d = os.path.join(BASE, "scripts", sub)
    print("\nRULE DIR", sub)
    for f in sorted(os.listdir(d)):
        if f.endswith(".py") and f != "__init__.py":
            path = os.path.join(d, f)
            with open(path, encoding="utf-8") as fh:
                lines = fh.readlines()
            sigs = [ln.strip() for ln in lines if ln.lstrip().startswith(("def ", "class "))]
            print(f"{f}: {len(lines)} lines; signatures={sigs}")
            print("".join(lines[:40]))

# Compute MFA from Ragni2016 by transforming tasks/responses if possible.
rag = pd.read_csv(os.path.join(BASE, "Ragni2016.csv"))
print("\nRagni shape", rag.shape, "participants", rag["id"].nunique(), "unique task strings", rag["task"].nunique())
print("responses top:", rag["response"].value_counts().head(15).to_dict())
print("tasks per sequence unique counts:", rag.groupby("sequence")["task"].nunique().describe().to_dict())
print("sequences:", rag["sequence"].nunique(), sorted(rag["sequence"].unique())[:10], sorted(rag["sequence"].unique())[-10:])

valid = pd.read_csv(os.path.join(BASE, "valid_syllogisms.csv"))
print("\nvalid_syllogisms true count:", int(valid["is_valid"].sum()), "false count:", int((~valid["is_valid"]).sum()))
print(valid.head(20).to_string(index=False))