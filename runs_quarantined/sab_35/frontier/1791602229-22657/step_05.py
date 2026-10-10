#!/usr/bin/env python3
import os
import warnings
import numpy as np
import pandas as pd
import neurokit2 as nk

warnings.filterwarnings("ignore")

path = "benchmark/datasets/biosignals/bio_eventrelated_100hz.csv"
fs = 100
df = pd.read_csv(path)
rsp = df["RSP"].astype(float).to_numpy()

print("Input samples:", len(rsp), "duration_s:", len(rsp)/fs)
print("Running nk.rsp_process...")
signals, info = nk.rsp_process(rsp, sampling_rate=fs, method="khodadad2018")
print("signals shape:", signals.shape)
print("signals columns:", list(signals.columns))
print("info keys:", list(info.keys()))
for k, v in info.items():
    if isinstance(v, (list, np.ndarray, pd.Series)):
        arr = np.asarray(v)
        print(k, "len", len(arr), "first10", arr[:10])
    else:
        print(k, type(v), v)

print("\nNonzero counts in marker columns:")
for c in signals.columns:
    if c.endswith("_Peaks") or c.endswith("_Troughs"):
        inds = np.where(signals[c].values == 1)[0]
        print(c, len(inds), inds[:20])

print("\nHead selected columns:")
print(signals.head(20).to_string())

print("\nTrying rsp_intervalrelated...")
try:
    out = nk.rsp_intervalrelated(signals, sampling_rate=fs)
    print("intervalrelated type:", type(out), "shape:", getattr(out, "shape", None))
    print(out.to_string())
    print("columns:", list(out.columns))
except Exception as e:
    print("rsp_intervalrelated error:", repr(e))

print("\nTrying individual complexity helpers maybe available...")
for fn in ["entropy_sample", "entropy_approximate", "fractal_dfa", "fractal_correlation", "complexity_lempelziv"]:
    print(fn, hasattr(nk, fn))