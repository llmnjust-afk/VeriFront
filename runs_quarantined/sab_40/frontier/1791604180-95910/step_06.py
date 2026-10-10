#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import os

base = Path("benchmark/datasets/dili_MD")
print("README candidates:")
for p in [Path("benchmark/README.md"), base.parent/"dili/README.md", base/"README.md"]:
    if p.exists():
        print("\n---", p, "---")
        print(p.read_text(errors="ignore")[:2000])

meta = pd.read_csv(base/"standardized_compounds_excl_ambiguous_cluster.csv")
desc = pd.read_csv(base/"mol_descriptors_training.csv")
test = pd.read_csv(base/"test.csv")
print("\nmeta shape", meta.shape, "desc shape", desc.shape, "test shape", test.shape)
print("vDILIConcern counts:")
print(meta["vDILIConcern"].value_counts(dropna=False).to_string())
print("\ncluster counts summary:")
print(meta["cluster"].describe().to_string())
print("clusters with >1 count head:")
print(meta["cluster"].value_counts().head(20).to_string())
print("\nTest cols first/last:")
print(list(test.columns[:15]))
print(list(test.columns[-15:]))
print("test index-like", [c for c in test.columns if c.startswith("Unnamed") or c==""])
cand = [c for c in test.columns if any(s in c.lower() for s in ["label","dili","concern","split","cluster","cid","compound","smiles","class","name"])]
print("test metadata candidates:", cand)
if cand:
    print(test[cand].head().to_string())
print("test numeric/nonnum", test.select_dtypes("number").shape[1], test.select_dtypes(exclude="number").shape[1])
print("test missing total", int(test.isna().sum().sum()))
print("train missing total", int(desc.isna().sum().sum()))
print("train columns equal test?", list(desc.columns)==list(test.columns))
print("columns in train not test:", list(set(desc.columns)-set(test.columns))[:20])
print("columns in test not train:", list(set(test.columns)-set(desc.columns))[:20])

# inspect alternative dili dir
for d in ["benchmark/datasets/dili"]:
    p=Path(d)
    if p.exists():
        print("\nAlternative", d, "files", [x.name for x in p.iterdir()])
        for fn in ["train.csv","test.csv"]:
            q=p/fn
            if q.exists():
                df=pd.read_csv(q)
                print(q, df.shape, list(df.columns))
                print(df.head().to_string())
                for c in df.columns:
                    if any(s in c.lower() for s in ["dili","label","concern"]):
                        print(c, df[c].value_counts(dropna=False).to_string())