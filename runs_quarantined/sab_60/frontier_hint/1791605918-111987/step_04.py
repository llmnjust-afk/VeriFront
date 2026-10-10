#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

targets = {"Ragni2016.csv", "valid_syllogisms.csv", "accuracies_data_for_plot.csv", "ind_data_for_plot.csv",
           "PSYCOP.csv", "Matching.csv", "VerbalModels.csv", "MMT.csv", "Conversion.csv", "PHM.csv", "Atmosphere.csv"}
print("cwd", Path.cwd())

matches = []
for base in [Path("benchmark"), Path(".")]:
    print("Scanning", base)
    for dirpath, dirnames, filenames in os.walk(base):
        # Skip bulky image/cache dirs to keep output useful
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__"} and not d.lower().endswith("_images")]
        for fn in filenames:
            if fn in targets or fn.endswith(".py") and "rules" in dirpath.split(os.sep):
                matches.append(Path(dirpath) / fn)

print("matches", len(matches))
for p in sorted(matches)[:500]:
    print(p, p.stat().st_size)

# Search directory names containing nvc/syllog
print("\nRelevant directory names:")
count = 0
for base in [Path("benchmark"), Path(".")]:
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.lower().endswith("_images")]
        low = str(dirpath).lower()
        if any(k in low for k in ["nvc", "syllog", "ragni"]):
            print(dirpath)
            count += 1
            if count > 200:
                break

print("\nPreview candidate CSVs with target names:")
for p in sorted([m for m in matches if m.suffix == ".csv"])[:100]:
    print("\n==", p)
    try:
        df = pd.read_csv(p)
        print("shape", df.shape)
        print("cols", list(df.columns))
        print(df.head(3).to_string(index=False))
    except Exception as e:
        print("err", repr(e))