#!/usr/bin/env python3
import os
import pandas as pd

print("Working directory:", os.getcwd())
print("Top-level entries:", sorted(os.listdir(".")))

# Locate dataset
for candidate in [".", "benchmark", "/data/lab/VeriFront/runs/sab_60/frontier/1791601912-19348/benchmark"]:
    print("\nListing candidate:", candidate, "exists:", os.path.exists(candidate))
    if os.path.exists(candidate):
        for root, dirs, files in os.walk(candidate):
            rel = os.path.relpath(root, candidate)
            level = 0 if rel == "." else rel.count(os.sep) + 1
            if level > 4:
                dirs[:] = []
                continue
            indent = "  " * level
            print(f"{indent}{os.path.basename(root) if rel != '.' else candidate}/")
            for f in sorted(files)[:15]:
                print(f"{indent}  {f} ({os.path.getsize(os.path.join(root, f))} bytes)")

# find nvc directories
matches = []
for root, dirs, files in os.walk("."):
    if os.path.basename(root) == "nvc":
        matches.append(root)
print("\nFound nvc dirs:", matches)

base = matches[0] if matches else "benchmark/nvc"
print("Using base:", base)

# Inspect key CSVs
paths = [
    f"{base}/valid_syllogisms.csv",
    f"{base}/accuracies_data_for_plot.csv",
    f"{base}/ind_data_for_plot.csv",
    f"{base}/Ragni2016.csv",
    f"{base}/scripts/indiv_table/models/PSYCOP.csv",
    f"{base}/scripts/prediction_errors/models/PSYCOP.csv",
]
for path in paths:
    print("\n---", path, "---")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            print("shape:", df.shape)
            print("columns:", list(df.columns))
            print(df.head(12).to_string(index=False))
        except Exception as e:
            print("Could not read:", repr(e))
    else:
        print("missing")

# Inspect all model files briefly
for sub in ["scripts/indiv_table/models", "scripts/prediction_errors/models"]:
    d = os.path.join(base, sub)
    print("\nMODEL DIR", d, os.path.isdir(d))
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            path = os.path.join(d, fn)
            try:
                df = pd.read_csv(path)
                print(fn, df.shape, list(df.columns), "head:", df.head(3).to_dict("records"))
            except Exception as e:
                print(fn, "ERR", e)

# Inspect rule scripts
for subdir in ["scripts/indiv_table/rules", "scripts/prediction_errors/rules", "scripts/nvc_prediction/rules"]:
    d = os.path.join(base, subdir)
    print("\nRULE DIR", d, os.path.isdir(d))
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".py"):
                path = os.path.join(d, fn)
                print("\n---", path, "---")
                with open(path, "r", encoding="utf-8") as f:
                    print(f.read()[:2500])