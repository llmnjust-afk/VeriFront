#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import re

base = Path("benchmark/datasets/dili_MD")
desc = pd.read_csv(base/"mol_descriptors_training.csv")
meta = pd.read_csv(base/"standardized_compounds_excl_ambiguous_cluster.csv")
test = pd.read_csv(base/"test.csv")

print("desc shape", desc.shape)
print("meta shape", meta.shape)
print("test shape", test.shape)
print("\nMeta vDILIConcern counts:")
print(meta["vDILIConcern"].value_counts(dropna=False).to_string())
print("\nMeta cluster summary:", meta["cluster"].describe().to_string(), "nunique", meta["cluster"].nunique())
print("\nTest columns all:")
print(list(test.columns))
print("\nTest head first 8 cols:")
print(test.iloc[:10, :min(12, test.shape[1])].to_string())
print("\nTest tail cols:")
print(test.iloc[:5, max(0,test.shape[1]-12):].to_string())
print("Test labelish:")
for c in [c for c in test.columns if any(s in c.lower() for s in ["dili","label","split","concern","cluster","cid","compound","smile"])]:
    print(c, test[c].dtype, test[c].nunique(dropna=False), test[c].value_counts(dropna=False).head(10).to_dict())

# Compare descriptor columns train/test
train_cols = list(desc.columns)
test_cols = list(test.columns)
print("\nTrain descriptor first/last:", train_cols[:5], train_cols[-5:])
print("Test first/last:", test_cols[:5], test_cols[-5:])
print("cols in train not test (first 30):", [c for c in train_cols if c not in test_cols][:30], "count", len([c for c in train_cols if c not in test_cols]))
print("cols in test not train (first 30):", [c for c in test_cols if c not in train_cols][:30], "count", len([c for c in test_cols if c not in train_cols]))

# Inspect relevant gold/eval files by grep snippets
terms = ["dili_MD", "MD_MCNC", "MCLCNC", "MCNC", "mol_descriptors_training", "vDILIConcern"]
for root in [Path("benchmark/gold_programs"), Path("benchmark/eval_programs"), Path("benchmark/scoring_rubrics")]:
    print(f"\nRelevant files under {root}:")
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.stat().st_size < 1000000:
            try:
                txt = p.read_text(errors="replace")
            except Exception:
                continue
            if any(t.lower() in txt.lower() or t.lower() in str(p).lower() for t in terms):
                print("FILE", p, "size", p.stat().st_size)
                low = txt.lower()
                # print lines containing terms
                lines = txt.splitlines()
                hits = []
                for i,line in enumerate(lines):
                    if any(t.lower() in line.lower() for t in terms):
                        hits.append((i+1,line[:300]))
                for i,line in hits[:30]:
                    print(f"  L{i}: {line}")