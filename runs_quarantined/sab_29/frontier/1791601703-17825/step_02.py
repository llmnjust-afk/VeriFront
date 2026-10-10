#!/usr/bin/env python3
import os
import glob
import pandas as pd
import numpy as np
import importlib.util

print("Working directory:", os.getcwd())

# Search for the dataset in likely locations.
patterns = [
    "biosignals/bio_eventrelated_100hz.csv",
    "../biosignals/bio_eventrelated_100hz.csv",
    "../../biosignals/bio_eventrelated_100hz.csv",
    "../../../biosignals/bio_eventrelated_100hz.csv",
    "/data/lab/VeriFront/**/*.csv",
    "/data/**/*.csv",
]
matches = []
for pat in patterns:
    found = glob.glob(pat, recursive=True)
    print(f"Pattern {pat!r}: {len(found)} matches")
    for x in found[:20]:
        print("  ", x)
    matches.extend(found)

target = None
for x in matches:
    if os.path.basename(x) == "bio_eventrelated_100hz.csv":
        target = x
        break

if target is None:
    print("\nNo target file found. Directory listing around cwd:")
    for p in ["..", "../..", "../../..", "/data/lab/VeriFront", "/data/lab/VeriFront/runs"]:
        if os.path.exists(p):
            print("\nLIST", p)
            try:
                for name in os.listdir(p)[:50]:
                    print(" ", name)
            except Exception as e:
                print("  ERROR", e)
    raise FileNotFoundError("Could not locate bio_eventrelated_100hz.csv")

print("\nUsing target:", target)
df = pd.read_csv(target)
print("Loaded shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head().to_string())
print(df.describe().T.to_string())

print("\nPackage availability:")
for pkg in ["neurokit2", "scipy", "numpy", "pandas"]:
    spec = importlib.util.find_spec(pkg)
    print(f"  {pkg}: {'available' if spec else 'NOT available'}")

if "Photosensor" in df.columns:
    ps = df["Photosensor"].to_numpy()
    vals, counts = np.unique(ps, return_counts=True)
    print("\nPhotosensor unique count:", len(vals), "min/max:", np.nanmin(ps), np.nanmax(ps))
    print("First unique values/counts:")
    for v, c in zip(vals[:20], counts[:20]):
        print(f"  {v!r}: {c}")
    idx = np.where(np.abs(np.diff(ps)) > 1e-9)[0] + 1
    print("Number of photosensor changes:", len(idx))
    print("First 80 changes index,time_s,from,to:")
    for i in idx[:80]:
        print(f"  {i}, {i/100:.2f}, {ps[i-1]!r} -> {ps[i]!r}")
    change_points = np.r_[0, idx, len(ps)]
    runs = [(a, b, (b-a)/100.0, ps[a]) for a, b in zip(change_points[:-1], change_points[1:])]
    print("\nRuns count:", len(runs))
    print("First 50 runs start,end,dur_s,value:")
    for r in runs[:50]:
        print(" ", r)
    print("Last 20 runs:")
    for r in runs[-20:]:
        print(" ", r)

os.makedirs("pred_results", exist_ok=True)
with open("pred_results/data_path.txt", "w") as f:
    f.write(target + "\n")
print("\nSaved pred_results/data_path.txt")