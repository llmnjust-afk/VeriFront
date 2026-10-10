#!/usr/bin/env python3
"""
Inspect questionnaire dataframe structure and benchmark gold program/evaluator to
determine exact expected PSS scoring/output format.
"""
from pathlib import Path
import pandas as pd
import pickle

data_file = Path("benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl")
gold_program = Path("benchmark/gold_programs/questionnaire.py")
eval_program = Path("benchmark/eval_programs/biopsykit_questionnaire_eval.py")
gold_csv = Path("benchmark/eval_programs/gold_results/biopsykit_questionnaire_gold.csv")

print("CWD:", Path.cwd())
print("Data exists:", data_file.exists(), data_file)

df = pd.read_pickle(data_file)
print("\nLoaded df")
print("type:", type(df))
print("shape:", df.shape)
print("index type:", type(df.index))
print("index name:", df.index.name)
print("index first 10:", list(df.index[:10]))
print("columns n:", len(df.columns))
print("columns first 80:", list(df.columns[:80]))
print("columns repr:", repr(list(df.columns[:15])))
print("\nhead:")
print(df.head().to_string())

print("\nPSS cols present:")
for c in [f"PSS_{i:02d}" for i in range(1, 11)]:
    print(c, c in df.columns, df[c].head().tolist() if c in df.columns else None)

if gold_program.exists():
    print("\n--- gold_programs/questionnaire.py ---")
    print(gold_program.read_text()[:5000])
else:
    print("No gold program found")

if eval_program.exists():
    print("\n--- eval_programs/biopsykit_questionnaire_eval.py ---")
    print(eval_program.read_text()[:5000])
else:
    print("No eval program found")

if gold_csv.exists():
    print("\n--- gold csv head ---")
    g = pd.read_csv(gold_csv, header=None)
    print("shape:", g.shape)
    print(g.head(10).to_string(index=False, header=False))
    print("dtypes:", g.dtypes.tolist())
else:
    print("No gold csv found")

# Compute both plausible subscale variants for first rows for comparison.
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
pss = df[pss_cols].apply(pd.to_numeric)
helpless = pss[["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]].sum(axis=1)
self_raw = pss[["PSS_04", "PSS_05", "PSS_07", "PSS_08"]].sum(axis=1)
self_rev = (4 - pss[["PSS_04", "PSS_05", "PSS_07", "PSS_08"]]).sum(axis=1)
print("\nFirst 10 manual variants:")
tmp = pd.DataFrame({
    "subject_index": df.index.astype(str),
    "helpless_direct": helpless,
    "self_raw": self_raw,
    "self_rev": self_rev,
    "total_direct_plus_rev": helpless + self_rev,
    "total_direct_plus_raw": helpless + self_raw,
})
print(tmp.head(10).to_string(index=False))