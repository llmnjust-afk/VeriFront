#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("CWD:", Path.cwd())

# List dataset directory names to locate DILI dataset
ds = Path("benchmark/datasets")
if ds.exists():
    names = sorted([p.name for p in ds.iterdir() if p.is_dir()])
    print("Number of dataset dirs:", len(names))
    print("Dataset dirs containing dili/md/liver/drug/chem:")
    for name in names:
        low = name.lower()
        if any(s in low for s in ["dili", "liver", "drug", "chem", "md"]):
            print(" ", name)
    print("First 100 dataset dirs:", names[:100])
    print("Last 100 dataset dirs:", names[-100:])

# Targeted searches for file/folder names (avoid huge verbose output)
targets = ["mol_descriptors_training.csv", "standardized_compounds_excl_ambiguous_cluster.csv", "test.csv"]
found = []
for p in ds.rglob("*") if ds.exists() else []:
    low = str(p).lower()
    if ("dili" in low or "mol_descriptors" in low or "standardized_compounds" in low) and (p.is_file() or p.is_dir()):
        found.append(p)
print("\nTargeted found count:", len(found))
for p in found[:200]:
    try:
        print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size}")
    except Exception as e:
        print(" ", p, "ERR", e)

# Try likely location
candidates = [
    Path("benchmark/datasets/dili_MD"),
    Path("benchmark/datasets/DILI_MD"),
    Path("benchmark/datasets/dili"),
    Path("benchmark/datasets/DILI"),
]
for base in candidates:
    if base.exists():
        print("\nInspecting candidate", base)
        print(sorted([x.name for x in base.iterdir()])[:100])
        for fname in targets:
            path = base / fname
            print(fname, "exists", path.exists())
            if path.exists():
                df = pd.read_csv(path)
                print(fname, "shape", df.shape, "cols first", list(df.columns[:10]), "cols last", list(df.columns[-10:]))