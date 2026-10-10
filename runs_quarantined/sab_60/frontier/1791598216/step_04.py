#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import os

base = Path("benchmark")
print("CWD:", Path.cwd())

# Targeted search for nvc dataset and expected files under benchmark.
targets = ["Ragni2016.csv", "valid_syllogisms.csv", "accuracies_data_for_plot.csv", "ind_data_for_plot.csv"]
for name in targets:
    hits = list(base.rglob(name))
    print(f"{name}: {len(hits)} hits")
    for h in hits[:10]:
        print(" ", h)

# Search directories named nvc
nvc_dirs = [p for p in base.rglob("*") if p.is_dir() and p.name.lower() == "nvc"]
print("nvc dirs:", len(nvc_dirs))
for p in nvc_dirs[:20]:
    print(" ", p)

# If no exact nvc, search CSVs with syllogistic-ish names/contents by path name
keywords = ["ragni", "syllog", "nvc", "psycop", "verbal", "atmosphere"]
matches = []
for p in base.rglob("*"):
    s = str(p).lower()
    if any(k in s for k in keywords):
        matches.append(p)
print("keyword path matches:", len(matches))
for p in sorted(matches)[:200]:
    print(" ", p)

# Locate expected model files by basename and parent path
model_names = ["PSYCOP.csv", "Matching.csv", "VerbalModels.csv", "MMT.csv", "Conversion.csv", "PHM.csv", "Atmosphere.csv"]
for name in model_names:
    hits = list(base.rglob(name))
    print(f"model {name}: {len(hits)}")
    for h in hits[:10]:
        print(" ", h)

# If dataset exists in benchmark/datasets, list plausible small top-level dataset names only
ds = base / "datasets"
if ds.exists():
    dirs = [p.name for p in ds.iterdir() if p.is_dir()]
    print("number dataset dirs", len(dirs))
    print("dataset dirs containing relevant keyword:", [d for d in dirs if any(k in d.lower() for k in keywords)])
    print("first 100 dataset dirs:", sorted(dirs)[:100])