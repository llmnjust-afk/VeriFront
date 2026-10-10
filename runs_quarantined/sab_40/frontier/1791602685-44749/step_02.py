#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("Working directory:", Path.cwd())
print("Top-level entries:", sorted([p.name for p in Path(".").iterdir()])[:100])

# Search for expected files under current directory and nearby common roots
expected = {"mol_descriptors_training.csv", "standardized_compounds_excl_ambiguous_cluster.csv", "test.csv"}
roots = [Path("."), Path(".."), Path("/data/lab/VeriFront")]
found = {}
for root in roots:
    if root.exists():
        print(f"\nSearching under {root.resolve()} ...")
        count = 0
        try:
            for p in root.rglob("*"):
                if p.name in expected:
                    found.setdefault(p.name, []).append(p)
                    print("FOUND", p.name, "at", p)
                count += 1
                if count > 200000:
                    print("Search limit reached for", root)
                    break
        except Exception as e:
            print("Search error for", root, repr(e))

print("\nFound summary:", {k: [str(x) for x in v] for k, v in found.items()})

# If found, inspect the first complete folder candidate
if all(k in found for k in expected):
    paths = {k: found[k][0] for k in expected}
    print("\nUsing paths:", {k: str(v) for k, v in paths.items()})
    for fname, path in paths.items():
        print("\n==", fname, "==")
        df = pd.read_csv(path)
        print("shape:", df.shape)
        print("columns first 15:", list(df.columns[:15]))
        print("columns last 15:", list(df.columns[-15:]))
        labelish = [c for c in df.columns if any(s in c.lower() for s in ["dili", "label", "split", "class", "concern", "cluster", "cid", "compound", "smile"])]
        print("label/split-ish columns:", labelish[:50])
        print(df.iloc[:3, :min(8, df.shape[1])].to_string())
        for c in labelish[:12]:
            print(f"  {c} vc:", df[c].value_counts(dropna=False).head(8).to_dict())
else:
    print("Could not find all expected files.")