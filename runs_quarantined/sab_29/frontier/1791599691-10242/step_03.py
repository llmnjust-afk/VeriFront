#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd

path = "benchmark/datasets/biosignals/bio_eventrelated_100hz.csv"
df = pd.read_csv(path)
print("Loaded", path, "shape", df.shape)
print("Columns:", list(df.columns))
print(df.head().to_string())
print(df.tail().to_string())

fs = 100
duration = len(df)/fs
print("Duration seconds:", duration, "minutes:", duration/60)

# Photosensor detailed inspection
ph = df["Photosensor"].to_numpy(dtype=float)
print("\nPhotosensor min/max/mean/std:", np.nanmin(ph), np.nanmax(ph), np.nanmean(ph), np.nanstd(ph))
vals, counts = np.unique(ph, return_counts=True)
print("Unique photosensor values:", len(vals))
if len(vals) <= 100:
    for v,c in zip(vals, counts):
        print(f"  {v!r}: {c}")
else:
    print("First 30 unique:", vals[:30])
    print("Last 30 unique:", vals[-30:])

# Segment by exact photosensor plateaus/changes
changes = np.where(np.diff(ph) != 0)[0] + 1
starts = np.r_[0, changes]
ends = np.r_[changes, len(ph)]
print("\nExact photosensor segments:", len(starts))
for i,(s,e) in enumerate(zip(starts[:80], ends[:80])):
    print(f"seg {i:03d}: samples {s}-{e-1}, t {s/fs:.2f}-{e/fs:.2f}s, dur {(e-s)/fs:.2f}s, val {ph[s]}")

# Threshold-based transitions to infer event starts/ends
for thr in [0.1,0.5,1,2,2.5,3,4,4.5]:
    binary = ph > thr
    changes = np.where(np.diff(binary.astype(int)) != 0)[0] + 1
    print(f"\nThreshold > {thr}: {len(changes)} changes")
    print("changes:", [(int(i), round(i/fs,2), int(binary[i])) for i in changes[:60]])
    if len(changes)>0:
        seg_starts = np.r_[0, changes]
        seg_ends = np.r_[changes, len(binary)]
        ons = []
        for s,e in zip(seg_starts, seg_ends):
            if binary[s]:
                ons.append((s,e,(e-s)/fs))
        print("ON segments first 30:", [(s,e,round(d,2)) for s,e,d in ons[:30]])

# Basic availability of processing packages
for mod in ["neurokit2", "scipy"]:
    try:
        m = __import__(mod)
        print(f"\n{mod} version:", getattr(m, "__version__", "unknown"))
    except Exception as e:
        print(f"\n{mod} import failed:", repr(e))