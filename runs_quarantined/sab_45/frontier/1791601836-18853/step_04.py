#!/usr/bin/env python3
"""
Targeted search for the questionnaire dataset within the benchmark directory and
nearby filesystem, then compute PSS if found.
"""
from pathlib import Path
import os
import pickle
import pandas as pd

search_roots = [
    Path("."),
    Path("benchmark"),
    Path("benchmark/datasets"),
    Path("/data/lab/VeriFront/runs/sab_45/frontier/1791601836-18853/benchmark"),
    Path("/data/lab/VeriFront/runs/sab_45/frontier/1791601836-18853/benchmark/datasets"),
]

print("CWD:", Path.cwd())
print("Targeted search roots:")
for r in search_roots:
    print(" ", r, "exists=", r.exists())

# Search by name fragments and likely extensions
matches = []
fragments = ["questionnaire", "biopsykit", "pss", "PSS"]
for root in search_roots:
    if not root.exists():
        continue
    try:
        for p in root.rglob("*"):
            name = p.name
            full = str(p)
            if any(frag.lower() in name.lower() or frag.lower() in full.lower() for frag in fragments):
                matches.append(p)
    except Exception as e:
        print(f"Search error in {root}: {e}")

# Deduplicate preserving order
dedup = []
seen = set()
for p in matches:
    s = str(p)
    if s not in seen:
        dedup.append(p)
        seen.add(s)

print(f"\nFound {len(dedup)} paths matching questionnaire/biopsykit/pss:")
for p in dedup[:200]:
    print(" ", p, "dir" if p.is_dir() else "file")

# Also print dataset directory names containing bio/question/stress
datasets = Path("benchmark/datasets")
if datasets.exists():
    print("\nDataset subdirectories with relevant names:")
    for p in sorted([x for x in datasets.iterdir() if x.is_dir()]):
        n = p.name.lower()
        if any(k in n for k in ["bio", "question", "stress", "pss", "psy"]):
            print(" ", p)

# Pick a likely data file
data_file = None
for p in dedup:
    if p.is_file() and p.name == "questionnaire_data.pkl":
        data_file = p
        break
if data_file is None:
    for p in dedup:
        if p.is_file() and p.suffix.lower() in [".pkl", ".pickle", ".csv", ".parquet", ".tsv"]:
            data_file = p
            break

if data_file is None:
    # Generate a compact listing of all pkl files under benchmark/datasets for diagnosis
    print("\nNo obvious file found. Listing all pickle files under benchmark/datasets:")
    pkls = list(Path("benchmark/datasets").rglob("*.pkl")) if Path("benchmark/datasets").exists() else []
    for p in pkls[:300]:
        print(" ", p)
    print("Total pickle files:", len(pkls))
    raise FileNotFoundError("questionnaire_data.pkl not found in targeted search")

print("\nUsing data file:", data_file)

# Load data
if data_file.suffix.lower() in [".pkl", ".pickle"]:
    try:
        df = pd.read_pickle(data_file)
    except Exception:
        with open(data_file, "rb") as f:
            df = pickle.load(f)
elif data_file.suffix.lower() == ".csv":
    df = pd.read_csv(data_file)
elif data_file.suffix.lower() == ".tsv":
    df = pd.read_csv(data_file, sep="\t")
elif data_file.suffix.lower() == ".parquet":
    df = pd.read_parquet(data_file)
else:
    raise ValueError(f"Unsupported data file suffix: {data_file.suffix}")

print("Loaded object type:", type(df))
print("Shape:", getattr(df, "shape", None))
if not isinstance(df, pd.DataFrame):
    raise TypeError("Loaded object is not a pandas DataFrame")
print("Columns:", list(df.columns)[:80])
print("Head:")
print(df.head().to_string(index=False))

pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
missing = [c for c in ["subject"] + pss_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns in selected data file: {missing}")

pss = df[pss_cols].apply(pd.to_numeric, errors="raise")
helplessness_items = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
self_efficacy_items = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

# PSS total contribution: direct helplessness + reverse-scored positive/self-efficacy items.
perceived_helplessness = pss[helplessness_items].sum(axis=1)
perceived_self_efficacy = (4 - pss[self_efficacy_items]).sum(axis=1)
total_pss = perceived_helplessness + perceived_self_efficacy

result = pd.DataFrame({
    "subject": df["subject"],
    "perceived_helplessness": perceived_helplessness.astype(int),
    "perceived_self_efficacy": perceived_self_efficacy.astype(int),
    "total_pss": total_pss.astype(int),
})

out_path = Path("pred_results/questionnaire_pred.csv")
out_path.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(out_path, index=False, header=False)

print("\nSaved:", out_path.resolve())
print("Output shape:", result.shape)
print(result.head(12).to_string(index=False))
print(result[["perceived_helplessness", "perceived_self_efficacy", "total_pss"]].describe().to_string())