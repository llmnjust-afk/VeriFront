import pandas as pd
import numpy as np
from pathlib import Path

train = pd.read_csv("benchmark/datasets/dkpes/dkpes_train.csv")
y = train["Signal-inhibition"].astype(float).values

print("All train Signal-inhibition values sorted:")
vals = np.sort(y)
print(vals)
print("\nSorted with gaps:")
for i, v in enumerate(vals):
    gap = vals[i+1] - v if i < len(vals)-1 else np.nan
    print(f"{i:02d}: {v:.3f} gap_to_next={gap:.3f}")

print("\nCounts above candidate thresholds:")
for t in [0.3,0.4,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9]:
    print(f"t={t:.2f}: positives={(y>=t).sum()} negatives={(y<t).sum()}")

print("\nTrain rows sorted by Signal-inhibition:")
cols = ["index","Signal-inhibition","ShapeQuery","3-Keto","3-Hydroxy","12-Keto","12-Hydroxy","19-Methyl","18-Methyl","Sulfate-Ester","Sulfate-Oxygens","Sulfur","TanimotoCombo","ComboScore","Overlap"]
print(train.sort_values("Signal-inhibition")[cols].to_string(index=False))