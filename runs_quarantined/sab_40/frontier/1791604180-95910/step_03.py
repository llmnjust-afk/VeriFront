#!/usr/bin/env python3
import os
from pathlib import Path

print("cwd:", os.getcwd())
b = Path("benchmark")
print("benchmark exists:", b.exists(), "is_dir:", b.is_dir())
if b.exists():
    print("benchmark listing:")
    for p in sorted(b.rglob("*")):
        rel = p.relative_to(Path("."))
        if p.is_file():
            print(" FILE", rel, p.stat().st_size)
        else:
            print(" DIR ", rel)

print("\nFind csv/pkl/parquet/json files under benchmark:")
if b.exists():
    for p in sorted(b.rglob("*")):
        if p.is_file() and p.suffix.lower() in [".csv", ".pkl", ".pickle", ".parquet", ".json", ".tsv"]:
            print(p, p.stat().st_size)