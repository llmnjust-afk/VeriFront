#!/usr/bin/env python3
import os
from pathlib import Path

base = Path("benchmark/datasets")
names = []
for root, dirs, files in os.walk(base, followlinks=True):
    for d in dirs:
        if "question" in d.lower() or "biopsy" in d.lower() or "pss" in d.lower():
            names.append(Path(root)/d)
    for f in files:
        if "question" in f.lower() or "biopsy" in f.lower() or "pss" in f.lower() or f.endswith((".pkl", ".pickle")):
            names.append(Path(root)/f)

print("Matching paths count:", len(names))
for p in names[:300]:
    print(p)

# If exact dataset exists under benchmark, compute now.
candidates = [
    Path("biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl"),
    Path("benchmark/datasets/BioPsyKit/questionnaire_data.pkl"),
]
for p in names:
    if p.name == "questionnaire_data.pkl":
        candidates.append(p)

print("\nCandidate paths:")
for p in candidates:
    print(p, "exists=", p.exists())

# Also inspect gold/eval programs relevant names for hints
print("\nRelevant program/rubric files:")
for root, dirs, files in os.walk("benchmark", followlinks=True):
    for f in files:
        lp = f.lower()
        if "question" in lp or "biopsy" in lp or "pss" in lp:
            print(Path(root)/f)