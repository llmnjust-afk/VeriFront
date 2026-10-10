#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

base = Path("benchmark")
print("Benchmark exists:", base.exists())
print("Benchmark tree up to depth 6:")
for p in sorted(base.rglob("*")):
    if len(p.relative_to(base).parts) <= 6:
        print(" ", p, "dir" if p.is_dir() else "file")

print("\nReading CSV candidates:")
for f in sorted(base.rglob("*.csv")):
    print("\nFILE", f)
    try:
        df = pd.read_csv(f)
        print("shape", df.shape, "columns", list(df.columns))
        print(df.head(5).to_string(index=False))
    except Exception as e:
        print("ERR", repr(e))

print("\nReading Python rule candidates first 120 lines:")
for f in sorted(base.rglob("*.py")):
    print("\nPY", f)
    try:
        txt = f.read_text()
        print("\n".join(txt.splitlines()[:120]))
    except Exception as e:
        print("ERR", repr(e))