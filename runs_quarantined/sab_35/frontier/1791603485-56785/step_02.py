#!/usr/bin/env python3
import os
from pathlib import Path
import importlib.util

print("Working directory:", os.getcwd())
print("Top-level listing:")
for p in sorted(Path(".").iterdir()):
    print(" -", p, "dir" if p.is_dir() else f"{p.stat().st_size} bytes")

print("\nSearching for bio_eventrelated_100hz.csv under current tree and common parents...")
search_roots = [Path("."), Path(".."), Path("../.."), Path("/data/lab")]
seen = set()
matches = []
for root in search_roots:
    try:
        root_res = root.resolve()
        if root_res in seen:
            continue
        seen.add(root_res)
        print("Scanning", root_res)
        for p in root.rglob("bio_eventrelated_100hz.csv"):
            matches.append(p.resolve())
            print(" FOUND:", p.resolve())
    except Exception as e:
        print(" Could not scan", root, ":", repr(e))

print("Total matches:", len(matches))
for pkg in ["numpy", "pandas", "scipy", "neurokit2"]:
    print(f"Package {pkg}:", "available" if importlib.util.find_spec(pkg) else "NOT available")

if matches:
    import pandas as pd
    f = matches[0]
    df = pd.read_csv(f)
    print("\nUsing first match:", f)
    print("Loaded shape:", df.shape)
    print("Columns:", list(df.columns))
    print(df.head().to_string())
    print(df["RSP"].describe().to_string())
    Path("pred_results").mkdir(exist_ok=True)
    Path("pred_results/data_path.txt").write_text(str(f))
    print("Saved selected data path to pred_results/data_path.txt")
else:
    print("No input CSV found yet.")