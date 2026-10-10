#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("Find DKPES-related benchmark program/rubric files with concise previews")
for root in ["benchmark/gold_programs", "benchmark/eval_programs", "benchmark/scoring_rubrics"]:
    p = Path(root)
    print("\nROOT", root, "exists", p.exists())
    if not p.exists():
        continue
    candidates = [f for f in p.rglob("*") if f.is_file() and ("dkpes" in f.name.lower() or "dkpes" in str(f).lower())]
    print("num candidates", len(candidates))
    for f in candidates:
        print("CANDIDATE", f, "size", f.stat().st_size)
        try:
            txt = f.read_text(errors="ignore")
            lines = txt.splitlines()
            for i, line in enumerate(lines[:120], 1):
                print(f"{i:03d}: {line[:220]}")
        except Exception as e:
            print("read error", repr(e))

print("\nSearch all text files for dkpes_test_pred mention (limited)")
hits = []
for root in ["benchmark"]:
    for f in Path(root).rglob("*"):
        if f.is_file() and f.stat().st_size < 500000:
            try:
                txt = f.read_text(errors="ignore")
            except Exception:
                continue
            if "dkpes_test_pred" in txt or "Signal-inhibition" in txt and "dkpes" in str(f).lower():
                hits.append(f)
print("hits", [str(h) for h in hits[:50]])
for f in hits[:20]:
    print("\nHIT", f)
    txt = f.read_text(errors="ignore")
    idx = txt.find("dkpes_test_pred")
    if idx < 0:
        idx = txt.find("Signal-inhibition")
    print(txt[max(0, idx-1000):idx+2000])

train = pd.read_csv("benchmark/datasets/dkpes/dkpes_train.csv")
print("\nTrain target stats precise:")
print(train["Signal-inhibition"].describe())
print("Sorted values:", train["Signal-inhibition"].sort_values().tolist())
print("Above candidate thresholds counts:")
for thr in [0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8]:
    print(thr, int((train["Signal-inhibition"]>=thr).sum()), "/", len(train))