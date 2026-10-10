#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

out = Path("pred_results/accuracies.csv")
df = pd.read_csv(out)
print("Final file exists:", out.exists())
print("Final file size bytes:", out.stat().st_size)
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("\nOverall means:")
print(df[["hit_model", "hit_nvc", "improvement"]].mean().to_string())

print("\nRows per model:")
print(df.groupby("model").size().to_string())

print("\nRows per NVC rule:")
print(df.groupby("nvc").size().to_string())

print("\nMean improvement by NVC rule:")
print(df.groupby("nvc")["improvement"].mean().sort_values(ascending=False).to_string())

print("\nBest model/rule combinations by mean improvement:")
summary = (
    df.groupby(["model", "nvc"], as_index=False)
    .agg(
        mean_hit_model=("hit_model", "mean"),
        mean_hit_nvc=("hit_nvc", "mean"),
        mean_improvement=("improvement", "mean"),
        n=("task", "count"),
    )
    .sort_values("mean_improvement", ascending=False)
)
print(summary.head(15).to_string(index=False))

print("\nWorst model/rule combinations by mean improvement:")
print(summary.tail(10).to_string(index=False))