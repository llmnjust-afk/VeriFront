#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import os

base = Path("benchmark/datasets/nvc")

print("Python files outside rules:")
for p in sorted((base/"scripts").rglob("*.py")):
    if "/rules/" not in str(p):
        print("\n==", p.relative_to(base))
        print(p.read_text(errors="replace")[:5000])

print("\nRule files (full, focused):")
for name in ["atmosphere.py","emptystart.py","figural.py","negativity.py","particularity.py","partneg.py"]:
    p = base/"scripts/nvc_prediction/rules"/name
    print("\n==", name, "size", p.stat().st_size)
    print(p.read_text(errors="replace"))

print("\naccuracies_data_for_plot summary")
ad = pd.read_csv(base/"accuracies_data_for_plot.csv")
print("shape", ad.shape)
print("cols", ad.columns.tolist())
print("head")
print(ad.head(12).to_string(index=False))
print("unique model", ad["model"].unique().tolist() if "model" in ad.columns else "no model col")
for col in ad.columns:
    if ad[col].dtype == object:
        print(col, "unique sample", ad[col].dropna().unique()[:20].tolist())

print("\nAll model accuracies_data grouping if applicable:")
print(ad.groupby([c for c in ["model","rule"] if c in ad.columns]).size().head(100).to_string())