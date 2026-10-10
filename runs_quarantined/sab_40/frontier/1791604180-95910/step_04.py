#!/usr/bin/env python3
import os
from pathlib import Path

root = Path("benchmark/datasets")
print("Searching benchmark/datasets for DILI/MD dataset-related files...")
patterns = []
count = 0
for dirpath, dirnames, filenames in os.walk(root):
    # prune very image-heavy dirs to keep output manageable, but don't prune possible dili dirs
    parts = Path(dirpath).parts
    low = str(dirpath).lower()
    if any(x in low for x in ["bbbc", "images"]) and "dili" not in low:
        # prevent descending into image directories
        dirnames[:] = [d for d in dirnames if "dili" in d.lower() or "md" == d.lower()]
    for f in filenames:
        fl = f.lower()
        path = Path(dirpath) / f
        s = str(path).lower()
        if ("dili" in s or "mol_descriptors" in fl or "standardized_compounds" in fl or fl == "test.csv") and path.suffix.lower() in [".csv",".pkl",".pickle",".parquet",".tsv"]:
            print(path, path.stat().st_size)
            count += 1
print("matched files:", count)

print("\nDataset directories containing 'dili' or named dili_MD:")
for p in root.rglob("*"):
    if p.is_dir() and ("dili" in p.name.lower() or p.name == "dili_MD"):
        print(p)