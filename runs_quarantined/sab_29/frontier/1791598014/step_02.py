#!/usr/bin/env python3
import os
import glob
import pandas as pd
import numpy as np

print("Working directory:", os.getcwd())
print("Top-level listing:")
print(os.listdir("."))

# Locate dataset robustly
candidates = []
for pattern in [
    "biosignals/bio_eventrelated_100hz.csv",
    "../biosignals/bio_eventrelated_100hz.csv",
    "../../biosignals/bio_eventrelated_100hz.csv",
    "../../../biosignals/bio_eventrelated_100hz.csv",
    "/data/lab/VeriFront/biosignals/bio_eventrelated_100hz.csv",
    "/data/lab/VeriFront/runs/biosignals/bio_eventrelated_100hz.csv",
    "/data/lab/VeriFront/**/*.csv",
    "/data/**/*.csv",
]:
    matches = glob.glob(pattern, recursive=True)
    for m in matches:
        if os.path.basename(m) == "bio_eventrelated_100hz.csv":
            candidates.append(m)

# Also limited walk upward/downward
for root in [".", "..", "../..", "../../..", "/data/lab/VeriFront"]:
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            if "bio_eventrelated_100hz.csv" in filenames:
                candidates.append(os.path.join(dirpath, "bio_eventrelated_100hz.csv"))
    except Exception as e:
        print("Walk error", root, e)

candidates = sorted(set(os.path.abspath(c) for c in candidates))
print("Candidates found:", candidates)
if not candidates:
    raise FileNotFoundError("Could not locate bio_eventrelated_100hz.csv")

path = candidates[0]
print("Using path:", path)
df = pd.read_csv(path)
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("Head:")
print(df.head().to_string(index=False))
print("Describe:")
print(df.describe().T.to_string())

# Inspect photosensor signal for event localization
fs = 100
photo = df["Photosensor"].to_numpy()
print("Photosensor unique count:", len(np.unique(photo)))
print("Photosensor min/max:", np.nanmin(photo), np.nanmax(photo))
uniq = np.unique(np.round(photo, 6))
print("First 30 unique rounded photosensor values:", uniq[:30])
print("Last 30 unique rounded photosensor values:", uniq[-30:])

p_round = np.round(photo, 6)
change_idx = np.where(np.diff(p_round) != 0)[0] + 1
run_starts = np.r_[0, change_idx]
run_ends = np.r_[change_idx, len(photo)]
runs = pd.DataFrame({
    "start_idx": run_starts,
    "end_idx": run_ends,
    "duration_s": (run_ends - run_starts) / fs,
    "value": p_round[run_starts],
})
print("Number of photosensor runs:", len(runs))
print("First 80 runs:")
print(runs.head(80).to_string(index=False))
print("Last 80 runs:")
print(runs.tail(80).to_string(index=False))

baseline = pd.Series(p_round).mode().iloc[0]
print("Photosensor mode baseline:", baseline)
nonbaseline_runs = runs[runs["value"] != baseline].copy()
print("Non-baseline runs count:", len(nonbaseline_runs))
print(nonbaseline_runs.head(200).to_string(index=False))

# Save discovered path for future turns
with open("dataset_path.txt", "w") as f:
    f.write(path + "\n")
print("Saved dataset_path.txt")