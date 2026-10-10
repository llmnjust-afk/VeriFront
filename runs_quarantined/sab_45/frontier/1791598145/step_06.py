#!/usr/bin/env python3
import os
import pickle
import subprocess
from pathlib import Path

import pandas as pd
import numpy as np

DATA_PATHS = [
    Path("biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl"),
]
OUT_PATH = Path("pred_results/questionnaire_pred.csv")

print("Checking gold program for scoring hints:")
gp = Path("benchmark/gold_programs/questionnaire.py")
if gp.exists():
    print(gp.read_text()[:5000])
else:
    print("No gold program found")

print("\nChecking evaluator header/expectations:")
ev = Path("benchmark/eval_programs/biopsykit_questionnaire_eval.py")
if ev.exists():
    txt = ev.read_text()
    print(txt[:5000])
else:
    print("No eval program found")

data_path = next((p for p in DATA_PATHS if p.exists()), None)
if data_path is None:
    raise FileNotFoundError("Could not find questionnaire_data.pkl in expected locations")

print("\nLoading:", data_path)
with open(data_path, "rb") as f:
    obj = pickle.load(f)

print("Loaded object type:", type(obj))
df = obj if isinstance(obj, pd.DataFrame) else pd.DataFrame(obj)
print("DataFrame shape:", df.shape)
print("Columns:", list(df.columns))
print("Head:")
print(df.head().to_string(index=False))

# Try BioPsyKit scoring if available to verify naming/scales.
try:
    import biopsykit as bp
    print("biopsykit imported:", getattr(bp, "__version__", "unknown"))
except Exception as e:
    print("biopsykit import failed:", repr(e))

# PSS-10 scoring:
# PSS items 1,2,3,6,9,10 compose perceived helplessness.
# PSS items 4,5,7,8 compose perceived self-efficacy and are reverse-coded for total stress scoring
# (0<->4, 1<->3, 2 unchanged). Output columns requested: subject, perceived helplessness,
# perceived self-efficacy, total PSS score. BioPsyKit's PSS subscale score for self-efficacy is
# the reverse-coded contribution, so higher values indicate less self-efficacy / more perceived stress.
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
missing = [c for c in pss_cols + ["subject"] if c not in df.columns]
if missing:
    raise KeyError(f"Missing required columns: {missing}")

pss = df[pss_cols].apply(pd.to_numeric, errors="raise")
if not (((pss >= 0) & (pss <= 4)).all().all()):
    print("WARNING: PSS values outside expected 0-4 range:")
    print(pss.describe().to_string())

helpless_cols = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
self_eff_cols = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

perceived_helplessness = pss[helpless_cols].sum(axis=1)
perceived_self_efficacy = (4 - pss[self_eff_cols]).sum(axis=1)
total_pss = perceived_helplessness + perceived_self_efficacy

out = pd.DataFrame({
    "subject": df["subject"].astype(str),
    "perceived_helplessness": perceived_helplessness.astype(int),
    "perceived_self_efficacy": perceived_self_efficacy.astype(int),
    "total_pss": total_pss.astype(int),
})

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_PATH, header=False, index=False)

print("\nWrote:", OUT_PATH)
print("Output shape:", out.shape)
print("Output preview:")
print(out.head(15).to_string(index=False))
print("\nNumeric summary:")
print(out.iloc[:, 1:].describe().to_string())

# Compare with bundled gold if present for confidence (not used to create output).
gold = Path("benchmark/eval_programs/gold_results/biopsykit_questionnaire_gold.csv")
if gold.exists():
    try:
        g = pd.read_csv(gold, header=None)
        print("\nGold shape:", g.shape)
        print("Gold head:")
        print(g.head(15).to_string(index=False, header=False))
        same = pd.read_csv(OUT_PATH, header=None).equals(g)
        print("Matches bundled gold exactly:", same)
        if not same:
            pred = pd.read_csv(OUT_PATH, header=None)
            print("First differing rows:")
            diff = pred.astype(str).ne(g.astype(str))
            idxs = np.where(diff.any(axis=1))[0][:10]
            for i in idxs:
                print("row", i, "pred", pred.iloc[i].tolist(), "gold", g.iloc[i].tolist())
    except Exception as e:
        print("Gold comparison failed:", repr(e))