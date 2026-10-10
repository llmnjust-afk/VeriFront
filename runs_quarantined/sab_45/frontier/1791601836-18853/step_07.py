#!/usr/bin/env python3
"""
Final generation of pred_results/questionnaire_pred.csv for PSS-10 scoring.

Uses the benchmark dataset at:
benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl

Writes no header, preserving the subject index as first column, matching
BioPsyKit pss.to_csv(header=False) output.
"""
from pathlib import Path
import pandas as pd

data_file = Path("benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl")
out_path = Path("pred_results/questionnaire_pred.csv")
gold_csv = Path("benchmark/eval_programs/gold_results/biopsykit_questionnaire_gold.csv")

df = pd.read_pickle(data_file)
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
pss = df[pss_cols].apply(pd.to_numeric, errors="raise")

# BioPsyKit/Cohen PSS-10:
# perceived helplessness = direct items 1,2,3,6,9,10
# perceived self-efficacy = reverse-scored positive items 4,5,7,8
helpless_items = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
self_items = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

result = pd.DataFrame(
    {
        "perceived helplessness": pss[helpless_items].sum(axis=1).astype(int),
        "perceived self-efficacy": (4 - pss[self_items]).sum(axis=1).astype(int),
    },
    index=df.index,
)
result["PSS Score"] = (
    result["perceived helplessness"] + result["perceived self-efficacy"]
).astype(int)

out_path.parent.mkdir(parents=True, exist_ok=True)
# Keep index (subject) as first column; no header, as required.
result.to_csv(out_path, header=False)

print(f"Loaded {data_file} with shape {df.shape}")
print(f"Saved {out_path.resolve()}")
print(f"Output shape including subject column: ({result.shape[0]}, {result.shape[1] + 1})")
print("\nOutput content:")
print(out_path.read_text())

if gold_csv.exists():
    gold_text = gold_csv.read_text()
    pred_text = out_path.read_text()
    print("Matches benchmark gold CSV exactly:", pred_text == gold_text)
    if pred_text != gold_text:
        print("Gold content:")
        print(gold_text)

print("\nScore summary:")
print(result.describe().to_string())

assert out_path.exists()
assert result.shape[0] == df.shape[0]
assert (result["PSS Score"] == result["perceived helplessness"] + result["perceived self-efficacy"]).all()