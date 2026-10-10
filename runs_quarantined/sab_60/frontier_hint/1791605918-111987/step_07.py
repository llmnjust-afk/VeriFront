#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

base = Path("benchmark/datasets/nvc")

print("valid_syllogisms:")
vs = pd.read_csv(base/"valid_syllogisms.csv")
print(vs.shape, vs.columns.tolist())
print(vs.to_string(index=False))

print("\nModel CSV schemas and rows:")
for f in sorted((base/"scripts/indiv_table/models").glob("*.csv")):
    df = pd.read_csv(f)
    print("\nFILE", f.name)
    print("shape", df.shape)
    print("columns", df.columns.tolist())
    print(df.to_string(index=False, max_rows=100))

print("\nRules full source:")
for f in sorted((base/"scripts/nvc_prediction/rules").glob("*.py")):
    if f.name == "__init__.py": 
        continue
    print("\nFILE", f.name)
    txt = f.read_text(errors="replace")
    print(txt)

print("\nUnique task count and example MFA computation")
rag = pd.read_csv(base/"Ragni2016.csv")
print("Ragni shape", rag.shape)
print("unique sequences", rag["sequence"].nunique())
print("rows per sequence head", rag.groupby("sequence").size().head().to_dict())
mfa = rag.groupby("sequence")["response"].agg(lambda s: s.value_counts().index[0]).reset_index(name="mfa")
print(mfa.head(20).to_string(index=False))
print("MFA NVC fraction", (mfa["mfa"]=="NVC").mean(), "N", len(mfa))
print("task per sequence sample:")
print(rag.drop_duplicates("sequence")[["sequence","task","choices"]].head(20).to_string(index=False))