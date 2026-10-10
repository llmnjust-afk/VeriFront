#!/usr/bin/env python3
import os
import pandas as pd

print("CWD:", os.getcwd())
for root, dirs, files in os.walk(".", topdown=True):
    # limit noisy hidden/cache dirs
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__"]]
    depth = root.count(os.sep)
    if depth <= 4:
        print(root, "dirs=", dirs[:10], "files=", files[:10])
    if depth > 5:
        dirs[:] = []

candidates = []
for root, dirs, files in os.walk("."):
    for f in files:
        if f in ("train.csv", "test.csv") or f.endswith(".csv"):
            candidates.append(os.path.join(root, f))
print("CSV candidates:", candidates)

for path in candidates:
    try:
        df = pd.read_csv(path, nrows=5)
        print("\n---", path, "---")
        print("columns:", list(df.columns))
        print(df.head().to_string())
    except Exception as e:
        print("Could not read", path, e)