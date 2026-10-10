#!/usr/bin/env python3
from pathlib import Path
import os, pandas as pd

print("cwd", Path.cwd())
for start in [Path("benchmark"), Path(".")]:
    print("\nTree under", start)
    for root, dirs, files in os.walk(start):
        rel = Path(root).relative_to(start)
        if len(rel.parts) > 6:
            dirs[:] = []
            continue
        indent = "  "*len(rel.parts)
        print(f"{indent}{Path(root).name}/")
        for f in sorted(files)[:20]:
            path=Path(root)/f
            print(f"{indent}  {f} ({path.stat().st_size})")
        if len(files)>20:
            print(f"{indent}  ... {len(files)-20} more files")

print("\nFind CSVs:")
csvs = []
for root, dirs, files in os.walk("."):
    rel = Path(root).relative_to(".")
    if len(rel.parts)>8:
        dirs[:] = []
        continue
    for f in files:
        if f.endswith(".csv") or f.endswith(".py"):
            csvs.append(Path(root)/f)
for p in csvs[:300]:
    print(p, p.stat().st_size)
print("total csv/py", len(csvs))

print("\nPreview likely CSVs")
for p in csvs:
    if p.suffix == ".csv":
        print("\n", p)
        try:
            df = pd.read_csv(p)
            print(df.shape, list(df.columns))
            print(df.head().to_string(index=False))
        except Exception as e:
            print("ERR", repr(e))