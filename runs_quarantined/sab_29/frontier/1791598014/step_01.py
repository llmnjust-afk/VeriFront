#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

path = "biosignals/bio_eventrelated_100hz.csv"
print("Working directory:", os.getcwd())
print("Exists:", os.path.exists(path))
df = pd.read_csv(path)
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head())
print(df.describe(include="all").T)

# Inspect photosensor signal for event localization
fs = 100
photo = df["Photosensor"].to_numpy()
print("Photosensor unique count:", len(np.unique(photo)))
print("Photosensor min/max:", np.nanmin(photo), np.nanmax(photo))
print("First 30 unique photosensor values:", np.unique(photo)[:30])
print("Last 30 unique photosensor values:", np.unique(photo)[-30:])

# Find transitions in photosensor and summarize runs
# Use rounded values to handle tiny numeric variations if any
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
print("First 50 runs:")
print(runs.head(50).to_string(index=False))
print("Last 50 runs:")
print(runs.tail(50).to_string(index=False))

# Candidate events: transitions away from baseline / low-to-high / high-to-low
baseline = pd.Series(p_round).mode().iloc[0]
print("Photosensor mode baseline:", baseline)
nonbaseline_runs = runs[runs["value"] != baseline].copy()
print("Non-baseline runs count:", len(nonbaseline_runs))
print(nonbaseline_runs.head(100).to_string(index=False))
print("Output target directory exists before:", os.path.exists("pred_results"))