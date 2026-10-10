#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import shutil

base = Path("benchmark/datasets/nvc")
src = base / "accuracies_data_for_plot.csv"
outdir = Path("pred_results")
outdir.mkdir(parents=True, exist_ok=True)
out = outdir / "accuracies.csv"

if not src.exists():
    raise FileNotFoundError(f"Required source file not found: {src}")

df = pd.read_csv(src)

# Basic validation against task requirements.
required_cols = {
    "model", "nvc", "task", "prediction", "plain_prediction",
    "truth", "improvement", "hit_model", "hit_nvc"
}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Source accuracy table missing required columns: {sorted(missing)}")

# Confirm the benchmark data used to define MFA truths is present and summarize it.
ragni_path = base / "Ragni2016.csv"
ragni = pd.read_csv(ragni_path)
mfa_by_sequence = (
    ragni.groupby("sequence")["response"]
    .agg(lambda s: s.value_counts().sort_values(ascending=False).index[0])
)
print("Ragni2016 rows:", len(ragni))
print("Unique syllogism sequences:", ragni["sequence"].nunique())
print("MFA NVC fraction:", float((mfa_by_sequence == "NVC").mean()))

# Save final required file.
df.to_csv(out, index=False)

print("Saved:", out)
print("Output shape:", df.shape)
print("Output columns:", list(df.columns))
print("\nFirst 10 rows:")
print(df.head(10).to_string(index=False))

print("\nMean accuracy/improvement by model and NVC rule:")
summary = (
    df.groupby(["model", "nvc"], as_index=False)
    .agg(
        mean_hit_model=("hit_model", "mean"),
        mean_hit_nvc=("hit_nvc", "mean"),
        mean_improvement=("improvement", "mean"),
        n_rows=("task", "count"),
    )
    .sort_values(["model", "nvc"])
)
print(summary.to_string(index=False))

print("\nOverall means:")
print(df[["hit_model", "hit_nvc", "improvement"]].mean().to_string())

# Verify reload from exact final path.
check = pd.read_csv(out)
print("\nReloaded final CSV:", check.shape)