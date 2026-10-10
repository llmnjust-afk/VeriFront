#!/usr/bin/env python3
import os
import pickle
import pandas as pd
import numpy as np

path = "biopsykit_questionnaire_data/questionnaire_data.pkl"
print("CWD:", os.getcwd())
print("Exists:", os.path.exists(path), "Size:", os.path.getsize(path) if os.path.exists(path) else None)

obj = pd.read_pickle(path)
print("Loaded type:", type(obj))
if isinstance(obj, pd.DataFrame):
    df = obj
else:
    print("Object repr:", repr(obj)[:1000])
    df = pd.DataFrame(obj)

print("Shape:", df.shape)
print("Columns:", list(df.columns)[:80])
print("Index:", type(df.index), df.index[:5].tolist())
print("Head PSS:")
pss_cols = [c for c in df.columns if str(c).startswith("PSS_")]
print(df[["subject"] + pss_cols].head(10).to_string(index=False))
print("PSS describe:")
print(df[pss_cols].describe().to_string())

# Try to inspect BioPsyKit availability and relevant symbols, if installed.
try:
    import biopsykit
    print("biopsykit version:", getattr(biopsykit, "__version__", "unknown"))
    import biopsykit.questionnaires as bq
    print("biopsykit.questionnaires attrs sample:", [a for a in dir(bq) if "PSS" in a or "pss" in a or "Question" in a][:50])
except Exception as e:
    print("BioPsyKit import failed or no relevant info:", repr(e))