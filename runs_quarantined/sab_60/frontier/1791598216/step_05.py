#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

root = Path("benchmark/datasets/nvc")
print("root", root, root.exists())

# Inspect key CSV structures compactly
for p in [
    root/"valid_syllogisms.csv",
    root/"accuracies_data_for_plot.csv",
    root/"ind_data_for_plot.csv",
    root/"Ragni2016.csv",
]:
    df = pd.read_csv(p)
    print("\nCSV", p.name, "shape", df.shape)
    print("columns:", list(df.columns))
    print(df.head(8).to_string(index=False))

for sub in ["scripts/indiv_table/models", "scripts/prediction_errors/models"]:
    print("\nMODEL DIR", sub)
    for f in sorted((root/sub).glob("*.csv")):
        df = pd.read_csv(f)
        print("\n", f.name, "shape", df.shape, "cols", list(df.columns))
        print(df.head(8).to_string(index=False))

# Inspect scripts nearby (not giant)
print("\nPython scripts under nvc/scripts excluding rules/models:")
for f in sorted((root/"scripts").rglob("*.py")):
    if "/rules/" in str(f) or f.name == "__init__.py":
        continue
    print("\n---", f.relative_to(root), "---")
    txt = f.read_text()
    print("\n".join(txt.splitlines()[:220]))

# Inspect one set of rule functions
for sub in ["scripts/nvc_prediction/rules", "scripts/prediction_errors/rules", "scripts/indiv_table/rules"]:
    print("\nRULE SET", sub)
    for f in sorted((root/sub).glob("*.py")):
        if f.name == "__init__.py": continue
        print("\n---", f.name, "---")
        print("\n".join(f.read_text().splitlines()[:160]))