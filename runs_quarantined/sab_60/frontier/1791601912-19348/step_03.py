#!/usr/bin/env python3
import os, glob
import pandas as pd

# Targeted search for nvc directory/files under benchmark
hits = []
for root, dirs, files in os.walk("benchmark"):
    if os.path.basename(root) == "nvc":
        hits.append(root)
    if "Ragni2016.csv" in files or "valid_syllogisms.csv" in files:
        hits.append(root)
print("hits:", hits[:20], "count", len(hits))

# Also glob likely locations
patterns = [
    "benchmark/**/nvc",
    "benchmark/**/Ragni2016.csv",
    "benchmark/**/valid_syllogisms.csv",
    "benchmark/**/PSYCOP.csv",
]
for pat in patterns:
    m = glob.glob(pat, recursive=True)
    print(pat, "->", len(m), m[:10])

base = None
for p in glob.glob("benchmark/**/Ragni2016.csv", recursive=True):
    base = os.path.dirname(p)
    break
if base is None:
    for p in glob.glob("benchmark/**/valid_syllogisms.csv", recursive=True):
        base = os.path.dirname(p)
        break
print("base:", base)

if base:
    # list nvc tree compactly
    for root, dirs, files in os.walk(base):
        rel = os.path.relpath(root, base)
        level = 0 if rel == "." else rel.count(os.sep)+1
        if level > 4:
            dirs[:] = []
            continue
        print("  "*level + (os.path.basename(root) if rel != "." else base) + "/")
        for f in sorted(files):
            print("  "*level + f"  {f} ({os.path.getsize(os.path.join(root,f))})")
    
    # read csvs
    for rel in ["valid_syllogisms.csv", "accuracies_data_for_plot.csv", "ind_data_for_plot.csv", "Ragni2016.csv"]:
        path = os.path.join(base, rel)
        print("\n---", path, "---")
        if os.path.exists(path):
            df = pd.read_csv(path)
            print("shape", df.shape)
            print("cols", list(df.columns))
            print(df.head(8).to_string(index=False))
    
    # model dirs
    for sub in ["scripts/indiv_table/models", "scripts/prediction_errors/models"]:
        d = os.path.join(base, sub)
        print("\nMODEL DIR", d, os.path.isdir(d))
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                path=os.path.join(d,fn)
                df=pd.read_csv(path)
                print("\n", fn, df.shape, list(df.columns))
                print(df.head(5).to_string(index=False))
    
    # rules summaries first 1200
    for sub in ["scripts/indiv_table/rules", "scripts/prediction_errors/rules", "scripts/nvc_prediction/rules"]:
        d=os.path.join(base, sub)
        print("\nRULE DIR", d, os.path.isdir(d))
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".py") and fn!="__init__.py":
                    path=os.path.join(d,fn)
                    with open(path, encoding="utf-8") as f:
                        txt=f.read()
                    print(f"\n--- {sub}/{fn} len={len(txt)} ---\n{txt[:1200]}")