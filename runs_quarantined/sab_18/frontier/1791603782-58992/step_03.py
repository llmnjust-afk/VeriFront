#!/usr/bin/env python3
import os
import glob
import subprocess
from pathlib import Path

print("CWD:", os.getcwd())
print("benchmark exists:", os.path.exists("benchmark"), "isdir:", os.path.isdir("benchmark"), "islink:", os.path.islink("benchmark"))
try:
    print("benchmark listing:", os.listdir("benchmark"))
except Exception as e:
    print("benchmark listing error:", repr(e))

# Search likely nearby locations without being too broad
search_roots = [
    ".",
    "..",
    "../..",
    "/data/lab/VeriFront/runs/sab_18/frontier",
    "/data/lab/VeriFront",
    "/data/lab",
]
seen = set()
for sr in search_roots:
    if not os.path.exists(sr) or sr in seen:
        continue
    seen.add(sr)
    print(f"\nSearching root {sr}")
    matches = []
    for pattern in ["**/dili/train.csv", "**/train.csv", "**/dili/*.csv", "**/*dili*/*.csv"]:
        try:
            found = glob.glob(os.path.join(sr, pattern), recursive=True)
            matches.extend(found[:50])
        except Exception as e:
            print("glob error", pattern, e)
    # unique
    uniq = []
    for m in matches:
        if m not in uniq:
            uniq.append(m)
    print("matches count", len(uniq))
    for m in uniq[:100]:
        print(m)

# Also use find with maxdepth where available
for sr in ["/data/lab/VeriFront", "/data/lab"]:
    if os.path.exists(sr):
        print(f"\nfind under {sr}")
        try:
            res = subprocess.run(["find", sr, "-maxdepth", "6", "-type", "f", "-name", "train.csv"], capture_output=True, text=True, timeout=20)
            print(res.stdout[:5000])
            if res.stderr:
                print("stderr:", res.stderr[:1000])
        except Exception as e:
            print("find failed:", repr(e))