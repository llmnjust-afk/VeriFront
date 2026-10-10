#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
root = Path("benchmark/datasets/nvc")

# Compact inspect model CSVs
for sub in ["scripts/indiv_table/models", "scripts/prediction_errors/models"]:
    print("\nMODEL DIR", sub)
    for f in sorted((root/sub).glob("*.csv")):
        df = pd.read_csv(f)
        print(f.name, "shape", df.shape, "cols", list(df.columns))
        print(df.head(3).to_string(index=False))

# Locate and inspect non-rule scripts
print("\nAll py files under nvc/scripts:")
for f in sorted((root/"scripts").rglob("*.py")):
    print(f.relative_to(root))

print("\nNon-rule scripts full-ish:")
for f in sorted((root/"scripts").rglob("*.py")):
    if "rules" in f.parts or f.name == "__init__.py":
        continue
    print("\n---", f.relative_to(root), "---")
    lines = f.read_text().splitlines()
    for i, line in enumerate(lines[:300], 1):
        print(f"{i:03d}: {line}")

# Rules: signatures / class names / functions only
print("\nRule file definitions:")
for sub in ["scripts/nvc_prediction/rules", "scripts/prediction_errors/rules", "scripts/indiv_table/rules"]:
    print("\nRULE SET", sub)
    for f in sorted((root/sub).glob("*.py")):
        if f.name == "__init__.py": continue
        lines = f.read_text().splitlines()
        defs = [line for line in lines if line.strip().startswith(("class ", "def "))]
        print(f.name, defs)
        print("first 50:")
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:03d}: {line}")