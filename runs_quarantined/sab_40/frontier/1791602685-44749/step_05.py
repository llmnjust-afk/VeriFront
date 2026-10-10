#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np

base = Path("benchmark/datasets/dili_MD")
print("Using dataset folder:", base.resolve())

desc = pd.read_csv(base/"mol_descriptors_training.csv")
meta = pd.read_csv(base/"standardized_compounds_excl_ambiguous_cluster.csv")
test = pd.read_csv(base/"test.csv")

for name, df in [("desc", desc), ("meta", meta), ("test", test)]:
    print(f"\n{name} shape={df.shape}")
    print("columns:", list(df.columns[:25]), "...", list(df.columns[-25:]))
    print("head:")
    print(df.iloc[:5, :min(12, df.shape[1])].to_string())
    labelish = [c for c in df.columns if any(s in c.lower() for s in ["dili","label","split","concern","cluster","cid","compound","smile","mcnc","mclcnc"])]
    print("labelish:", labelish)
    for c in labelish:
        print(f"{c}: dtype={df[c].dtype}, nunique={df[c].nunique(dropna=False)}, vc={df[c].value_counts(dropna=False).head(20).to_dict()}")

print("\nIndex/Unnamed checks")
for name, df in [("desc", desc), ("meta", meta), ("test", test)]:
    un = [c for c in df.columns if c.startswith("Unnamed")]
    print(name, "unnamed", un)
    for c in un:
        print(c, "first10", df[c].head(10).tolist(), "unique?", df[c].is_unique)

print("\nNaN/inf checks")
for name, df in [("desc", desc), ("test", test)]:
    num = df.select_dtypes(include=[np.number])
    print(name, "numeric cols", num.shape[1], "NaN total", int(num.isna().sum().sum()), "inf total", int(np.isinf(num.to_numpy()).sum()))
    nonnum = [c for c in df.columns if c not in num.columns]
    print(name, "nonnum cols", nonnum[:20], "count", len(nonnum))

# Inspect possible gold/eval programs for expected output columns/split names
for root in [Path("benchmark/gold_programs"), Path("benchmark/eval_programs"), Path("benchmark/scoring_rubrics")]:
    print(f"\nSearching text under {root}")
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in [".py",".md",".txt",".json",".yaml",".yml",".csv"] and p.stat().st_size < 200000:
            txt = p.read_text(errors="replace")
            low = txt.lower()
            if any(s in low for s in ["dili_md", "md_mcnc", "mcnc", "mclcnc", "mol_descriptors"]):
                print("---", p, "---")
                print(txt[:5000])