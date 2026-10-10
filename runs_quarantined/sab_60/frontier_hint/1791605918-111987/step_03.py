#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

print("cwd", Path.cwd())
bench = Path("benchmark")
print("benchmark exists", bench.exists())
for p in sorted(bench.rglob("*")):
    rel = p.relative_to(bench)
    if p.is_dir():
        print("DIR ", rel)
    else:
        print("FILE", rel, p.stat().st_size)

print("\nCSV previews:")
for f in sorted(bench.rglob("*.csv")):
    print("\n==", f)
    try:
        df = pd.read_csv(f)
        print("shape", df.shape)
        print("cols", list(df.columns))
        print(df.head(5).to_string(index=False))
    except Exception as e:
        print("err", repr(e))

print("\nPY file previews:")
for f in sorted(bench.rglob("*.py")):
    print("\n==", f)
    lines = f.read_text(errors="replace").splitlines()
    for line in lines[:100]:
        print(line)