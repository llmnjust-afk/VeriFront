#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd

print("cwd", os.getcwd())
print("benchmark tree:")
for p in sorted(Path("benchmark").rglob("*")):
    print(p, "DIR" if p.is_dir() else f"FILE {p.stat().st_size}")

# Try inspect any csv/py in benchmark
for f in sorted(Path("benchmark").rglob("*")):
    if f.is_file() and f.suffix.lower() in [".csv", ".py", ".txt", ".md"]:
        print("\n===", f, "===")
        try:
            if f.suffix.lower()==".csv":
                df=pd.read_csv(f)
                print("shape", df.shape)
                print("cols", list(df.columns))
                print(df.head(8).to_string(index=False))
            else:
                txt=f.read_text(errors="replace").splitlines()
                print("\n".join(txt[:80]))
        except Exception as e:
            print("ERR", repr(e))