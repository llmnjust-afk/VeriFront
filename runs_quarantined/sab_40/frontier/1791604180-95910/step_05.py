#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
from pathlib import Path

base = Path("benchmark/datasets/dili_MD")
print("base:", base.resolve())
for fn in ["mol_descriptors_training.csv", "standardized_compounds_excl_ambiguous_cluster.csv", "test.csv"]:
    path = base / fn
    print("\n===", path, "===")
    df = pd.read_csv(path)
    print("shape:", df.shape)
    print("first cols:", list(df.columns[:12]))
    print("last cols:", list(df.columns[-12:]))
    print("index-like columns:", [c for c in df.columns if c.startswith("Unnamed") or c == ""])
    cand = [c for c in df.columns if any(s in c.lower() for s in ["label","dili","concern","split","cluster","cid","compound","smiles","class","train"])]
    print("metadata candidates:", cand)
    for c in cand:
        vc = df[c].value_counts(dropna=False).head(20)
        print(f"\n{c} dtype={df[c].dtype} nunique={df[c].nunique(dropna=False)} counts:")
        print(vc.to_string())
    print("\nhead metadata/first8:")
    cols = cand if cand else list(df.columns[:8])
    print(df[cols[:12]].head().to_string())

# compare row counts
train_desc = pd.read_csv(base / "mol_descriptors_training.csv", nrows=2)
test = pd.read_csv(base / "test.csv", nrows=2)
meta = pd.read_csv(base / "standardized_compounds_excl_ambiguous_cluster.csv")
print("\nmeta full shape:", meta.shape)
print("meta vDILIConcern unique:", meta["vDILIConcern"].unique() if "vDILIConcern" in meta else None)
print("meta cluster max/min/nunique:", meta["cluster"].min() if "cluster" in meta else None, meta["cluster"].max() if "cluster" in meta else None, meta["cluster"].nunique() if "cluster" in meta else None)