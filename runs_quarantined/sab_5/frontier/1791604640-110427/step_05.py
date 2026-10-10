#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

train_path = Path("benchmark/datasets/dkpes/dkpes_train.csv")
test_path = Path("benchmark/datasets/dkpes/dkpes_test.csv")

print("Reading train/test...")
train = pd.read_csv(train_path)
test = pd.read_csv(test_path)
print("train shape", train.shape)
print("test shape", test.shape)
print("test columns:", list(test.columns))
print("test head:")
print(test.head(20).to_string())
if "Signal-inhibition" in test.columns:
    print("test has Signal-inhibition summary:")
    print(test["Signal-inhibition"].describe().to_string())
else:
    print("test does NOT have Signal-inhibition column")

print("\nTrain Signal-inhibition sorted:")
print(train[["index", "Signal-inhibition"]].sort_values("Signal-inhibition").to_string(index=False))

print("\nLooking for DKPES-specific scripts/rubrics:")
for root in ["benchmark/gold_programs", "benchmark/eval_programs", "benchmark/scoring_rubrics"]:
    p = Path(root)
    print("\nROOT", root, "exists", p.exists())
    if not p.exists():
        continue
    candidates = []
    for f in p.rglob("*"):
        if f.is_file() and ("dkpes" in f.name.lower() or "dkpes" in str(f).lower()):
            candidates.append(f)
    print("candidates:", [str(c) for c in candidates])
    for f in candidates[:10]:
        print(f"\n--- {f} (size {f.stat().st_size}) ---")
        try:
            txt = f.read_text(errors="ignore")
            print(txt[:8000])
        except Exception as e:
            print("read error:", repr(e))

print("\nPotential output files in pred_results:", os.listdir("pred_results") if os.path.exists("pred_results") else "no pred_results")