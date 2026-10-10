#!/usr/bin/env python3
import os, glob, importlib.util
import numpy as np
import pandas as pd

# Locate target (prefer saved from previous step)
target = None
if os.path.exists("pred_results/data_path.txt"):
    target = open("pred_results/data_path.txt").read().strip()
if not target or not os.path.exists(target):
    for x in glob.glob("/data/lab/VeriFront/**/benchmark/datasets/biosignals/bio_eventrelated_100hz.csv", recursive=True):
        target = x
        break
print("target:", target)

df = pd.read_csv(target)
print("shape:", df.shape)
print("columns:", df.columns.tolist())
print("head:\n", df.head(3).to_string(index=False))
print("tail:\n", df.tail(3).to_string(index=False))
print("duration_s:", len(df)/100)

for pkg in ["neurokit2", "scipy"]:
    print(pkg, importlib.util.find_spec(pkg) is not None)

ps = df["Photosensor"].to_numpy()
vals, counts = np.unique(ps, return_counts=True)
print("photosensor unique n/min/max:", len(vals), ps.min(), ps.max())
print("unique vals counts:", list(zip(vals.tolist(), counts.tolist()))[:50])
changes = np.where(np.diff(ps) != 0)[0] + 1
print("changes count:", len(changes))
print("changes all (idx,s,from,to):")
for i in changes:
    print(i, f"{i/100:.2f}", ps[i-1], "->", ps[i])
cp = np.r_[0, changes, len(ps)]
runs = [(a,b,(b-a)/100,ps[a]) for a,b in zip(cp[:-1], cp[1:])]
print("runs:")
for r in runs:
    print(r)

# Try neurokit event finding if installed.
if importlib.util.find_spec("neurokit2") is not None:
    import neurokit2 as nk
    print("nk version:", getattr(nk, "__version__", "unknown"))
    for thresh in ["auto", 2.5, 4.0, 1.0]:
        try:
            ev = nk.events_find(df["Photosensor"], threshold=thresh)
            print("\nevents_find threshold", thresh)
            for k,v in ev.items():
                print(k, np.asarray(v)[:20], "len", len(v))
        except Exception as e:
            print("events_find failed", thresh, repr(e))