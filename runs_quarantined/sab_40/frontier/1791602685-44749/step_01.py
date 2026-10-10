#!/usr/bin/env python3
import os
import pandas as pd
from pathlib import Path

base = Path("dili_MD")
print("Working directory:", Path.cwd())
print("Files in dili_MD:", sorted([p.name for p in base.glob("*")]))

for fname in ["mol_descriptors_training.csv", "standardized_compounds_excl_ambiguous_cluster.csv", "test.csv"]:
    path = base / fname
    print("\n==", fname, "==")
    df = pd.read_csv(path)
    print("shape:", df.shape)
    print("columns first 20:", list(df.columns[:20]))
    print("columns last 20:", list(df.columns[-20:]))
    print("dtypes counts:", df.dtypes.value_counts().to_dict())
    print("head small:")
    print(df.iloc[:5, :min(8, df.shape[1])].to_string())
    # label-ish columns
    labelish = [c for c in df.columns if any(s in c.lower() for s in ["dili", "label", "split", "class", "concern", "cluster", "cid", "compound"])]
    print("label/split-ish columns:", labelish[:50])
    for c in labelish[:10]:
        try:
            print(f"  {c} value_counts:", df[c].value_counts(dropna=False).head(10).to_dict())
        except Exception as e:
            print(f"  {c} value_counts error:", e)

# Check row-count relationships
try:
    desc = pd.read_csv(base / "mol_descriptors_training.csv")
    meta = pd.read_csv(base / "standardized_compounds_excl_ambiguous_cluster.csv")
    test = pd.read_csv(base / "test.csv")
    print("\nRow counts desc/meta/test:", len(desc), len(meta), len(test))
    print("Unnamed columns:", [c for c in desc.columns if c.startswith("Unnamed")], [c for c in meta.columns if c.startswith("Unnamed")], [c for c in test.columns if c.startswith("Unnamed")])
except Exception as e:
    print("Error during relationship checks:", repr(e))