#!/usr/bin/env python3
import os
import pandas as pd
base = "benchmark/datasets/nvc"

ind = pd.read_csv(f"{base}/ind_data_for_plot.csv")
print("ind_data_for_plot full:")
print(ind.to_string(index=False))
print("rows:", len(ind))

acc = pd.read_csv(f"{base}/accuracies_data_for_plot.csv")
print("\naccuracies unique models:", sorted(acc["model"].unique()))
print("accuracies unique nvc:", sorted(acc["nvc"].unique()))
print("num combinations:", acc[["model","nvc"]].drop_duplicates().shape[0])
print("combination counts:")
print(acc.groupby(["model","nvc"]).size().to_string())

rag = pd.read_csv(f"{base}/Ragni2016.csv")
print("\nRagni ids:", rag["id"].nunique(), "rows:", len(rag), "rows/id min max", rag.groupby("id").size().min(), rag.groupby("id").size().max())
print("sequence unique:", rag["sequence"].nunique(), "min", rag["sequence"].min(), "max", rag["sequence"].max())

print("\nRead model files details:")
for f in sorted(os.listdir(f"{base}/scripts/indiv_table/models")):
    path = f"{base}/scripts/indiv_table/models/{f}"
    df = pd.read_csv(path)
    print("\n", f, "shape", df.shape, "columns", list(df.columns))
    print(df.tail(5).to_string(index=False))

print("\nRule names/classes grep:")
for sub in ["indiv_table", "prediction_errors", "nvc_prediction"]:
    print("\n", sub)
    for f in sorted(os.listdir(f"{base}/scripts/{sub}/rules")):
        if f.endswith(".py"):
            path = f"{base}/scripts/{sub}/rules/{f}"
            with open(path, encoding="utf-8") as fh:
                lines = fh.readlines()
            interesting = [ln.rstrip() for ln in lines if ("class " in ln or "def " in ln or "name" in ln or "Rule" in ln)][:30]
            print(f, ":", interesting)