#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
import json

outdir = Path("pred_results")
print("pred_results listing:")
for p in sorted(outdir.glob("*")):
    print(p, p.stat().st_size)

required = outdir / "MD_MCNC_RF.csv"
print("\nRequired exists:", required.exists())
if required.exists():
    df = pd.read_csv(required)
    print("Required shape:", df.shape)
    print("Last columns:", list(df.columns[-5:]))
    print("Label counts:", df["label"].value_counts(dropna=False).to_dict() if "label" in df.columns else "NO LABEL COLUMN")
    print("First 10 labels:", df["label"].head(10).tolist() if "label" in df.columns else None)

summary_path = outdir / "MD_RF_training_summary.json"
print("\nSummary exists:", summary_path.exists())
if summary_path.exists():
    summary = json.loads(summary_path.read_text())
    print(json.dumps(summary, indent=2)[:4000])