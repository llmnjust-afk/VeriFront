#!/usr/bin/env python3
"""
Compute PSS-10 scores from the questionnaire dataset and save:
pred_results/questionnaire_pred.csv

Output columns (no header):
subject, perceived helplessness, perceived self-efficacy, total PSS score
"""
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

in_path = Path("biopsykit_questionnaire_data/questionnaire_data.pkl")
out_path = Path("pred_results/questionnaire_pred.csv")
out_path.parent.mkdir(parents=True, exist_ok=True)

# Load data
try:
    df = pd.read_pickle(in_path)
except Exception:
    with open(in_path, "rb") as f:
        df = pickle.load(f)

print(f"Loaded {in_path}")
print(f"Data type: {type(df)}")
print(f"Shape: {getattr(df, 'shape', None)}")
print("Columns:", list(df.columns)[:15], "...")

# Ensure required columns exist
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
missing = [c for c in ["subject"] + pss_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

pss = df[pss_cols].apply(pd.to_numeric, errors="raise")

# PSS-10 scoring:
# Negative/helplessness items are summed directly: 1,2,3,6,9,10.
# Positive/self-efficacy items are reverse scored for stress total: 4,5,7,8,
# using the standard 0-4 PSS response scale (reverse = 4 - response).
helplessness_items = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
self_efficacy_items = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

helplessness = pss[helplessness_items].sum(axis=1)
self_efficacy_reversed = (4 - pss[self_efficacy_items]).sum(axis=1)
total = helplessness + self_efficacy_reversed

result = pd.DataFrame({
    "subject": df["subject"],
    "perceived_helplessness": helplessness.astype(int),
    "perceived_self_efficacy": self_efficacy_reversed.astype(int),
    "total_pss": total.astype(int),
})

# Save without header and without index as requested
result.to_csv(out_path, index=False, header=False)

print(f"Saved results to {out_path}")
print(f"Result shape: {result.shape}")
print("First 10 rows:")
print(result.head(10).to_string(index=False))
print("Summary statistics:")
print(result[["perceived_helplessness", "perceived_self_efficacy", "total_pss"]].describe().to_string())

# Small consistency checks
assert out_path.exists(), f"Output file was not created: {out_path}"
assert (result["total_pss"] == result["perceived_helplessness"] + result["perceived_self_efficacy"]).all()
assert result.shape[0] == df.shape[0]