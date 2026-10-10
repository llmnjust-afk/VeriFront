#!/usr/bin/env python3
from pathlib import Path
import os, inspect
import pandas as pd

print("Searching for paths containing sleep or imu under benchmark and cwd...")
hits = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
    r = Path(root)
    if any(s in str(r).lower() for s in ["sleep", "imu"]):
        hits.append(r)
    for f in files:
        if any(s in f.lower() for s in ["sleep", "imu"]) or f.lower().endswith((".pkl",".pickle")):
            hits.append(r/f)
for p in hits[:300]:
    try:
        size = p.stat().st_size if p.is_file() else ""
    except Exception:
        size = "?"
    print(p, size)
print("hit count", len(hits))

print("\nFind exact sleep_data.pkl from /data/lab/VeriFront/runs/sab_44/frontier and /data/lab/VeriFront if feasible...")
for base in [Path("."), Path("/data/lab/VeriFront")]:
    count=0
    for root, dirs, files in os.walk(base):
        # prune very large known benchmark dirs except names that might contain sleep
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache", "node_modules"}]
        if "sleep_data.pkl" in files:
            p=Path(root)/"sleep_data.pkl"
            print("EXACT", p, p.stat().st_size)
            count+=1
        # keep output bounded
        if count > 20:
            break
    print("base", base, "exact count", count)

print("\nBioPsyKit pipeline details")
from biopsykit.sleep import sleep_processing_pipeline
print("module file:", sleep_processing_pipeline.__file__)
fun = sleep_processing_pipeline.predict_pipeline_acceleration
print("signature:", inspect.signature(fun))
src = inspect.getsource(fun)
print("source length:", len(src))
print(src[:6000])