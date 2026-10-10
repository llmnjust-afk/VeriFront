#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import inspect

from biopsykit.signals.ecg import EcgProcessor

data_dir = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/ecg_processing_data")
df = pd.read_pickle(data_dir / "ecg_data.pkl")
fs = float((data_dir / "sampling_rate.txt").read_text().strip())

print("Input shape:", df.shape, "fs:", fs)
print("Trying EcgProcessor pipeline...")

proc = EcgProcessor(df, sampling_rate=fs)
print("Processor created.")
print("Initial __dict__ keys:", sorted(proc.__dict__.keys()))
for k, v in proc.__dict__.items():
    if not k.startswith("_"):
        print(" attr", k, type(v))

try:
    proc.ecg_process(outlier_correction="all", errors="warn")
    print("ecg_process completed.")
except Exception as e:
    print("ecg_process failed:", type(e).__name__, repr(e))
    # try default
    try:
        proc.ecg_process(errors="warn")
        print("ecg_process default completed.")
    except Exception as e2:
        print("ecg_process default failed:", type(e2).__name__, repr(e2))
        raise

print("Post-process __dict__ keys:", sorted(proc.__dict__.keys()))
for k, v in proc.__dict__.items():
    print("KEY:", k, "TYPE:", type(v))
    if isinstance(v, dict):
        print("  dict keys:", list(v.keys())[:20])
        for kk, vv in list(v.items())[:5]:
            print("   ", kk, type(vv), getattr(vv, "shape", None))
            if hasattr(vv, "head"):
                print(vv.head())
    elif hasattr(v, "shape"):
        print("  shape:", v.shape)
        if hasattr(v, "head"):
            print(v.head())

print("\nProperties:")
for prop in ["ecg", "hr_result"]:
    try:
        val = getattr(proc, prop)
        print(prop, type(val), getattr(val, "shape", None))
        if isinstance(val, dict):
            print(" keys:", list(val.keys()))
            for kk, vv in list(val.items())[:3]:
                print("  ", kk, type(vv), getattr(vv, "shape", None))
                if hasattr(vv, "head"):
                    print(vv.head())
        elif hasattr(val, "head"):
            print(val.head())
    except Exception as e:
        print(prop, "error:", repr(e))

# Print callable plot method signatures if any
print("\nPotential plot methods:")
for name in dir(proc):
    if "plot" in name.lower() and not name.startswith("_"):
        obj = getattr(proc, name)
        print(name, type(obj))
        if callable(obj):
            try: print(" sig", inspect.signature(obj))
            except Exception: pass