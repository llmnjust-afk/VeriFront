#!/usr/bin/env python3
import os
import sys
import importlib.util
import pandas as pd
import numpy as np

print("Working directory:", os.getcwd())
print("Files:")
for root, dirs, files in os.walk("."):
    level = root.count(os.sep)
    if level <= 2:
        indent = "  " * level
        print(f"{indent}{os.path.basename(root) or '.'}/")
        for f in files[:20]:
            print(f"{indent}  {f}")

path = "biosignals/bio_eventrelated_100hz.csv"
df = pd.read_csv(path)
print("\nLoaded", path)
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head())
print(df.describe(include="all").T)

# Package availability
for pkg in ["neurokit2", "scipy", "numpy", "pandas"]:
    spec = importlib.util.find_spec(pkg)
    print(f"Package {pkg}: {'available' if spec is not None else 'NOT available'}")
    if spec is not None and pkg == "neurokit2":
        import neurokit2 as nk
        print("neurokit2 version:", getattr(nk, "__version__", "unknown"))

# Inspect photosensor for event structure
if "Photosensor" in df.columns:
    ps = df["Photosensor"].to_numpy()
    vals, counts = np.unique(ps, return_counts=True)
    print("\nPhotosensor unique values (up to 20):")
    for v, c in zip(vals[:20], counts[:20]):
        print(repr(v), c)
    print("n unique:", len(vals), "min/max:", np.nanmin(ps), np.nanmax(ps))
    d = np.diff(ps)
    idx = np.where(np.abs(d) > 1e-9)[0] + 1
    print("Number of photosensor changes:", len(idx))
    print("First 50 change indices/times/values:")
    for i in idx[:50]:
        print(i, i/100, ps[i-1], "->", ps[i])
    
    # Runs
    change_points = np.r_[0, idx, len(ps)]
    print("\nFirst 30 runs: start,end,dur_s,value")
    for a, b in zip(change_points[:-1], change_points[1:])[:30] if False else []:
        pass
    runs = []
    for a, b in zip(change_points[:-1], change_points[1:]):
        runs.append((a, b, (b-a)/100.0, ps[a]))
    for r in runs[:30]:
        print(r)
    print("Last 10 runs:")
    for r in runs[-10:]:
        print(r)

# Save a small metadata file for next turns
os.makedirs("pred_results", exist_ok=True)
with open("pred_results/inspection_done.txt", "w") as f:
    f.write("inspection complete\n")