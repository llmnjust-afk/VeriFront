#!/usr/bin/env python3
"""
Locate questionnaire_data.pkl, compute PSS-10 scores, and save:
pred_results/questionnaire_pred.csv

Output columns (no header):
subject, perceived helplessness, perceived self-efficacy, total PSS score
"""
from pathlib import Path
import os
import pickle
import pandas as pd

print("Current working directory:", Path.cwd())
print("Top-level directory listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p)

# Locate the input file robustly because the dataset may be mounted outside cwd.
candidate_paths = [
    Path("biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("../biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("../../biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("/data/lab/VeriFront/biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("/data/lab/VeriFront/runs/biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("/mnt/data/biopsykit_questionnaire_data/questionnaire_data.pkl"),
]
found = None
for c in candidate_paths:
    if c.exists():
        found = c
        break

if found is None:
    print("Searching under /data/lab/VeriFront for questionnaire_data.pkl ...")
    roots = [Path("."), Path(".."), Path("../.."), Path("/data/lab/VeriFront"), Path("/mnt/data")]
    seen = set()
    for root in roots:
        try:
            root_resolved = root.resolve()
        except Exception:
            root_resolved = root
        if str(root_resolved) in seen or not root.exists():
            continue
        seen.add(str(root_resolved))
        try:
            matches = list(root.rglob("questionnaire_data.pkl"))
        except Exception as e:
            print(f"Could not search {root}: {e}")
            matches = []
        if matches:
            print(f"Matches under {root}:")
            for m in matches[:20]:
                print(" ", m)
            found = matches[0]
            break

if found is None:
    raise FileNotFoundError("Could not locate questionnaire_data.pkl")

print(f"Using input file: {found}")

# Load data
try:
    df = pd.read_pickle(found)
except Exception:
    with open(found, "rb") as f:
        df = pickle.load(f)

print(f"Loaded data type: {type(df)}")
print(f"Shape: {getattr(df, 'shape', None)}")
print("First columns:", list(df.columns)[:20])

# Ensure required columns exist
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
missing = [c for c in ["subject"] + pss_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

pss = df[pss_cols].apply(pd.to_numeric, errors="raise")

# Standard PSS-10 subscales:
# perceived helplessness items: 1,2,3,6,9,10 (direct)
# perceived self-efficacy items: 4,5,7,8 (reverse-scored for stress contribution)
helplessness_items = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
self_efficacy_items = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

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

print(f"Saved results to: {out_path.resolve()}")
print(f"Result shape: {result.shape}")
print("First 10 output rows:")
print(result.head(10).to_string(index=False))
print("Score summary:")
print(result[["perceived_helplessness", "perceived_self_efficacy", "total_pss"]].describe().to_string())

assert out_path.exists()
assert len(result) == len(df)
assert (result["total_pss"] == result["perceived_helplessness"] + result["perceived_self_efficacy"]).all()