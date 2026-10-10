#!/usr/bin/env python3
import os
import pandas as pd

# Load questionnaire data from the benchmark dataset location.
data_path = "benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl"
if not os.path.exists(data_path):
    data_path = "biopsykit_questionnaire_data/questionnaire_data.pkl"

df = pd.read_pickle(data_path)

# PSS-10 scoring:
# Perceived Helplessness items: 1, 2, 3, 6, 9, 10 (not reversed)
# Perceived Self-Efficacy items: 4, 5, 7, 8 (reverse-scored on a 0-4 scale)
helpless_cols = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
selfeff_cols = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

helpless = df[helpless_cols].sum(axis=1)
selfeff = (4 - df[selfeff_cols]).sum(axis=1)
total = helpless + selfeff

# Subject is stored as the dataframe index in the provided pickle.
subjects = df.index if df.index.name == "subject" or "subject" not in df.columns else df["subject"]

result = pd.DataFrame({
    "subject": subjects,
    "perceived_helplessness": helpless.astype(int).values,
    "perceived_self_efficacy": selfeff.astype(int).values,
    "total_pss_score": total.astype(int).values,
})

os.makedirs("pred_results", exist_ok=True)
out_path = "pred_results/questionnaire_pred.csv"
result.to_csv(out_path, index=False, header=False)

print(f"Saved {out_path}")
print("Shape:", result.shape)
print(result.to_string(index=False))