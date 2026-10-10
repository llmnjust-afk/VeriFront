#!/usr/bin/env python3
import os
import pickle
import pandas as pd
import numpy as np

DATA_PATH = "biopsykit_questionnaire_data/questionnaire_data.pkl"
OUT_PATH = "pred_results/questionnaire_pred.csv"

print("Loading:", DATA_PATH)
with open(DATA_PATH, "rb") as f:
    obj = pickle.load(f)

print("Loaded object type:", type(obj))
if isinstance(obj, pd.DataFrame):
    df = obj
else:
    try:
        df = pd.DataFrame(obj)
    except Exception as e:
        raise RuntimeError(f"Could not convert loaded object to DataFrame: {e}")

print("DataFrame shape:", df.shape)
print("Columns:", list(df.columns)[:20], "... total", len(df.columns))
print("Index name:", df.index.name)
print("First rows:")
print(df.head().to_string())

# Inspect availability/version of BioPsyKit and any questionnaire/PSS helpers, if installed.
try:
    import biopsykit
    print("biopsykit version:", getattr(biopsykit, "__version__", "unknown"))
    import pkgutil
    submods = [m.name for m in pkgutil.iter_modules(biopsykit.__path__)]
    print("biopsykit submodules:", submods)
except Exception as e:
    print("BioPsyKit import failed or unavailable:", repr(e))

# Compute PSS-10 using standard scoring:
# Items are scored 0-4. Positively stated items 4, 5, 7, 8 are reverse-scored for stress.
# Perceived helplessness: items 1,2,3,6,9,10 (raw negative items).
# Perceived self-efficacy: items 4,5,7,8 reverse-scored so higher means lower self-efficacy / more stress contribution.
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
missing = [c for c in pss_cols if c not in df.columns]
if missing:
    raise KeyError(f"Missing PSS columns: {missing}")

work = df.copy()
for c in pss_cols:
    work[c] = pd.to_numeric(work[c], errors="raise")

reverse_cols = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]
helpless_cols = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]

rev = work[reverse_cols].apply(lambda s: 4 - s)
perceived_helplessness = work[helpless_cols].sum(axis=1)
perceived_self_efficacy = rev.sum(axis=1)
total_pss = perceived_helplessness + perceived_self_efficacy

if "subject" in work.columns:
    subject = work["subject"]
else:
    subject = work.index.to_series()

out = pd.DataFrame({
    "subject": subject.astype(str).values,
    "perceived_helplessness": perceived_helplessness.astype(int).values,
    "perceived_self_efficacy": perceived_self_efficacy.astype(int).values,
    "total_pss": total_pss.astype(int).values,
})

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
out.to_csv(OUT_PATH, index=False, header=False)

print("Wrote:", OUT_PATH)
print("Output shape:", out.shape)
print("Output preview:")
print(out.head(10).to_string(index=False))
print("Summary:")
print(out[["perceived_helplessness", "perceived_self_efficacy", "total_pss"]].describe().to_string())