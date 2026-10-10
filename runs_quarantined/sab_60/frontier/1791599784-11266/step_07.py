#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
root=Path("benchmark/datasets/nvc")

# Show complete model CSVs as compact summaries and complete rule source
for f in sorted((root/"scripts/indiv_table/models").glob("*.csv")):
    df=pd.read_csv(f)
    print("\nMODEL", f.name, "shape", df.shape, "columns", list(df.columns))
    print("first 10:", df.head(10).to_dict("records"))
    print("prediction value counts:")
    print(df["Prediction"].value_counts().to_string())

for f in sorted((root/"scripts/nvc_prediction/rules").glob("*.py")):
    print("\nRULE", f.name, "size", f.stat().st_size)
    print(f.read_text())
    
# Analyze existing accuracies rows/missing combinations
acc=pd.read_csv(root/"accuracies_data_for_plot.csv")
models=sorted(acc.model.unique())
rules=sorted(acc.nvc.unique())
tasks=sorted(pd.read_csv(root/"valid_syllogisms.csv").syllog)
print("\nACC shape", acc.shape, "models", models, "rules", rules, "tasks", len(tasks))
missing=[]
for m in models:
    for r in rules:
        have=set(acc[(acc.model==m)&(acc.nvc==r)].task)
        miss=sorted(set(tasks)-have)
        if miss:
            missing.append((m,r,miss))
print("missing combinations:", missing[:20], "count", len(missing))
print("duplicate model/rule/task rows", acc.duplicated(["model","nvc","task"]).sum())
print("sample rows tail")
print(acc.tail(12).to_string(index=False))
print("\nMean accuracies by model/rule:")
print(acc.groupby(["model","nvc"])[["hit_model","hit_nvc","improvement"]].mean().round(4).to_string())