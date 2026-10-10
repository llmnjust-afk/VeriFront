#!/usr/bin/env python3
from pathlib import Path
import os
import pandas as pd
import numpy as np
import inspect

print("CWD:", os.getcwd())

# Print benchmark README
readme = Path("benchmark/README.md")
if readme.exists():
    print("README:", readme.read_text(errors="ignore"))

# Targeted search for sleep_imu_data and sleep_data.pkl in sensible roots, with pruning/limits
roots = [Path("."), Path("benchmark"), Path(".."), Path("/data/lab/VeriFront/runs"), Path("/data/lab/VeriFront")]
matches = []
for root in roots:
    if not root.exists():
        continue
    print("Searching root:", root)
    count = 0
    try:
        for p in root.rglob("*"):
            count += 1
            name = p.name.lower()
            sp = str(p).lower()
            if name == "sleep_data.pkl" or "sleep_imu_data" in sp or ("sleep" in sp and p.suffix.lower() in [".pkl", ".pickle", ".csv", ".json"]):
                try:
                    matches.append((p, p.stat().st_size if p.is_file() else None, "dir" if p.is_dir() else "file"))
                except Exception as e:
                    matches.append((p, None, repr(e)))
            if count % 200000 == 0:
                print(" scanned", count, "under", root, "matches", len(matches))
            if count > 1000000:
                print(" limit reached for", root)
                break
    except Exception as e:
        print(" search error in", root, repr(e))
    print("Finished", root, "scanned", count, "matches so far", len(matches))

print("MATCHES:")
for m in matches[:200]:
    print(m)
print("Total matches:", len(matches))

# Inspect package source file path and selected source if needed
from biopsykit.sleep import sleep_processing_pipeline
print("BioPsyKit module:", sleep_processing_pipeline.__file__)
print("pipeline signature:", inspect.signature(sleep_processing_pipeline.predict_pipeline_acceleration))