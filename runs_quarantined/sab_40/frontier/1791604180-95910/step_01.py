#!/usr/bin/env python3
import os
import json
import pandas as pd
import numpy as np

base = "dili_MD"
print("Working directory:", os.getcwd())
print("Files in dili_MD:", os.listdir(base) if os.path.isdir(base) else "MISSING")

for fn in ["mol_descriptors_training.csv", "standardized_compounds_excl_ambiguous_cluster.csv", "test.csv"]:
    path = os.path.join(base, fn)
    print("\n===", fn, "===")
    if not os.path.exists(path):
        print("Missing")
        continue
    df_head = pd.read_csv(path, nrows=5)
    print("head shape:", df_head.shape)
    print("columns first 20:", list(df_head.columns[:20]))
    print("columns last 20:", list(df_head.columns[-20:]))
    print(df_head.iloc[:, :min(8, df_head.shape[1])].to_string())
    try:
        df = pd.read_csv(path)
        print("full shape:", df.shape)
        # Print candidate label/split/id columns
        cand = [c for c in df.columns if any(s in c.lower() for s in ["label","dili","concern","split","cluster","cid","compound","smiles","class"])]
        print("candidate metadata columns:", cand[:50])
        for c in cand[:20]:
            try:
                print(f"value counts for {c}:", df[c].value_counts(dropna=False).head(10).to_dict())
            except Exception as e:
                print(f"could not value_counts {c}: {e}")
        print("missing total:", int(df.isna().sum().sum()))
        print("numeric cols:", int(df.select_dtypes(include=[np.number]).shape[1]), "non-numeric cols:", int(df.select_dtypes(exclude=[np.number]).shape[1]))
    except Exception as e:
        print("Could not read full file:", repr(e))