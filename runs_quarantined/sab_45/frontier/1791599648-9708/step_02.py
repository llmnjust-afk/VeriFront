#!/usr/bin/env python3
import os
import glob
from pathlib import Path
import pandas as pd

print("CWD:", os.getcwd())
print("Top-level entries:", sorted(os.listdir("."))[:100])

patterns = [
    "biopsykit_questionnaire_data/questionnaire_data.pkl",
    "../biopsykit_questionnaire_data/questionnaire_data.pkl",
    "../../biopsykit_questionnaire_data/questionnaire_data.pkl",
    "/data/**/biopsykit_questionnaire_data/questionnaire_data.pkl",
    "/mnt/data/**/biopsykit_questionnaire_data/questionnaire_data.pkl",
    "/workspace/**/biopsykit_questionnaire_data/questionnaire_data.pkl",
]
matches = []
for pat in patterns:
    found = glob.glob(pat, recursive=True)
    print("Pattern", pat, "->", len(found), "matches")
    matches.extend(found)
matches = sorted(set(matches))
print("All matches:", matches[:20])

if not matches:
    # broader but bounded search from current parents
    for base in [Path("."), Path(".."), Path("../.."), Path("/data/lab")]:
        try:
            for p in base.rglob("questionnaire_data.pkl"):
                matches.append(str(p))
        except Exception as e:
            print("rglob failed", base, repr(e))
    matches = sorted(set(matches))
    print("Rglob matches:", matches[:50])

if matches:
    path = matches[0]
    print("Using path:", path, "size:", os.path.getsize(path))
    obj = pd.read_pickle(path)
    print("Loaded type:", type(obj))
    df = obj if isinstance(obj, pd.DataFrame) else pd.DataFrame(obj)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns)[:80])
    pss_cols = [c for c in df.columns if str(c).startswith("PSS_")]
    print("PSS cols:", pss_cols)
    print(df[["subject"] + pss_cols].head(10).to_string(index=False))
else:
    print("No questionnaire_data.pkl found.")