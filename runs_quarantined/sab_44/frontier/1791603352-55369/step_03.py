#!/usr/bin/env python3
import os
from pathlib import Path
import pandas as pd
import numpy as np
import inspect
import json

print("CWD:", os.getcwd())
print("Directory tree under benchmark:")
for p in sorted(Path("benchmark").rglob("*")):
    try:
        info = "dir" if p.is_dir() else f"file {p.stat().st_size} bytes"
    except Exception as e:
        info = repr(e)
    print(p, info)

print("\nSearch for pickle/data files in cwd and likely parents:")
roots = [Path("."), Path(".."), Path("/data/lab/VeriFront/runs/sab_44/frontier")]
seen = set()
for root in roots:
    if not root.exists():
        continue
    for pat in ["*.pkl", "*.pickle", "*.csv", "*.parquet", "*.json"]:
        for p in root.rglob(pat):
            if p in seen:
                continue
            seen.add(p)
            try:
                print(p.resolve(), p.stat().st_size)
            except Exception as e:
                print(p, e)

# Inspect helper functions/classes to understand expected output
from biopsykit.sleep import sleep_processing_pipeline
print("\nModule file:", sleep_processing_pipeline.__file__)
for name in ["compute_sleep_endpoints", "convert_acc_data_to_g", "ActivityCounts", "WearDetection", "RestPeriods", "SleepWakeDetection"]:
    obj = getattr(sleep_processing_pipeline, name, None)
    print("\n==", name, obj, "==")
    if obj is not None:
        try:
            print(inspect.signature(obj))
        except Exception as e:
            print("signature err", e)
        try:
            src = inspect.getsource(obj)
            print(src[:3000])
        except Exception as e:
            print("source err", e)