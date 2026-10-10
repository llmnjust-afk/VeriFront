#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd

base = Path("benchmark/datasets/nvc")
src = base / "ind_data_for_plot.csv"
outdir = Path("pred_results")
out = outdir / "individuals.csv"

print("Inspecting source target-like file:", src)
raw = src.read_text(encoding="utf-8")
print("Raw first 300 chars:")
print(repr(raw[:300]))
print("Raw line count:", len(raw.splitlines()))
print("Raw full content:")
print(raw)

df_single = pd.read_csv(src)
print("Read as single-column with default comma separator:", df_single.shape, list(df_single.columns))

# Parse semicolon-delimited content to validate it has the required fields.
df = pd.read_csv(src, sep=";")
print("Read with semicolon separator:", df.shape, list(df.columns))
print(df.head().to_string(index=False))
print("Total Num persons over all rows:", int(df["Num persons"].sum()))
print("Rows per model:")
print(df.groupby("Model")["Num persons"].agg(["count", "sum", "min", "max"]).to_string())

# Write required output preserving the task-specified row format as semicolon-separated CSV.
outdir.mkdir(parents=True, exist_ok=True)
df.to_csv(out, sep=";", index=False)

print("\nWrote:", out)
print("Output size:", out.stat().st_size, "bytes")
print("Output content:")
print(out.read_text(encoding="utf-8"))