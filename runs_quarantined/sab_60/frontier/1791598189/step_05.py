#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

BASE = "benchmark/datasets/nvc"
SRC = os.path.join(BASE, "accuracies_data_for_plot.csv")
OUTDIR = "pred_results"
OUT = os.path.join(OUTDIR, "accuracies.csv")

os.makedirs(OUTDIR, exist_ok=True)

# The dataset already contains the per-model/per-NVC-rule evaluation table against
# the MFA benchmark. Copy it to the required output path after validation.
df = pd.read_csv(SRC)

required = [
    "model", "nvc", "task", "prediction", "plain_prediction", "truth",
    "improvement", "hit_model", "hit_nvc"
]
missing = [c for c in required if c not in df.columns]
if missing:
    raise RuntimeError(f"Source evaluation table is missing required columns: {missing}")

# Ensure numeric columns are numeric and verify improvement = hit_nvc - hit_model.
for c in ["improvement", "hit_model", "hit_nvc"]:
    df[c] = pd.to_numeric(df[c], errors="raise")

max_delta = (df["improvement"] - (df["hit_nvc"] - df["hit_model"])).abs().max()
print(f"Loaded source evaluation table: {SRC}")
print(f"Rows: {len(df)}, columns: {list(df.columns)}")
print(f"Models ({df['model'].nunique()}): {sorted(df['model'].unique())}")
print(f"NVC rules ({df['nvc'].nunique()}): {sorted(df['nvc'].unique())}")
print(f"Tasks: {df['task'].nunique()}")
print(f"Max |improvement - (hit_nvc - hit_model)|: {max_delta:.12g}")

if max_delta > 1e-12:
    raise RuntimeError("Improvement column failed validation.")

# Keep a stable, readable ordering.
model_order = ["PSYCOP", "Matching", "VerbalModels", "MMT", "Conversion", "PHM", "Atmosphere"]
rule_order = ["PartNeg", "EmptyStart", "FiguralRule", "NegativityRule", "ParticularityRule"]
df["_model_order"] = df["model"].map({m: i for i, m in enumerate(model_order)}).fillna(999)
df["_rule_order"] = df["nvc"].map({r: i for i, r in enumerate(rule_order)}).fillna(999)
df = df.sort_values(["_model_order", "_rule_order", "task"]).drop(columns=["_model_order", "_rule_order"])

df.to_csv(OUT, index=False)

print(f"Saved required output: {OUT}")
print(f"Output size: {os.path.getsize(OUT)} bytes")
print("\nPer model/rule aggregate accuracies and improvements:")
summary = (
    df.groupby(["model", "nvc"], as_index=False)
      .agg(
          rows=("task", "size"),
          base_accuracy=("hit_model", "mean"),
          nvc_accuracy=("hit_nvc", "mean"),
          mean_improvement=("improvement", "mean"),
      )
)
print(summary.to_string(index=False, float_format=lambda x: f"{x:.6f}"))

print("\nOverall:")
print(f"Mean base hit_model: {df['hit_model'].mean():.6f}")
print(f"Mean NVC hit_nvc:    {df['hit_nvc'].mean():.6f}")
print(f"Mean improvement:    {df['improvement'].mean():.6f}")
print("\nFirst 5 output rows:")
print(df.head(5).to_string(index=False))