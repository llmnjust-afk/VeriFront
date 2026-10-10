#!/usr/bin/env python3
from pathlib import Path
import os, inspect, json
import pandas as pd
import numpy as np

print("Check likely roots for dataset directories/files:")
roots = [Path("/data"), Path("/data/lab"), Path("/tmp"), Path("/mnt/data"), Path.home()]
patterns = ["sleep_imu_data", "sleep_data.pkl", "*sleep*imu*", "*sleep_data*"]
for base in roots:
    print("\nROOT", base, "exists", base.exists())
    if not base.exists():
        continue
    for pat in patterns:
        found = []
        try:
            # rglob may be expensive; cap outputs
            for i, p in enumerate(base.rglob(pat)):
                found.append(p)
                if len(found) >= 20:
                    break
        except Exception as e:
            print(" pattern", pat, "error", repr(e))
            continue
        print(" pattern", pat, "count_shown", len(found))
        for p in found:
            try:
                print("  ", p, "dir" if p.is_dir() else p.stat().st_size)
            except Exception as e:
                print("  ", p, "?", e)

print("\nFull predict_pipeline_acceleration source:")
from biopsykit.sleep import sleep_processing_pipeline
src = inspect.getsource(sleep_processing_pipeline.predict_pipeline_acceleration)
print(src)

print("\ncompute_sleep_endpoints signature/source excerpt:")
from biopsykit.sleep.sleep_endpoints import compute_sleep_endpoints
print(inspect.signature(compute_sleep_endpoints))
print(inspect.getsource(compute_sleep_endpoints)[:5000])

print("\nRestPeriods source excerpt:")
try:
    from biopsykit.sleep.sleep_processing_pipeline.sleep_processing_pipeline import RestPeriods, WearDetection, ActivityCounts
    for cls in [RestPeriods, WearDetection, ActivityCounts]:
        print("CLASS", cls, inspect.signature(cls))
        print(inspect.getsource(cls)[:3000])
except Exception as e:
    print("classes error", repr(e))