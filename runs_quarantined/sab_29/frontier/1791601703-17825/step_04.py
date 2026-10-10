#!/usr/bin/env python3
import os, glob, warnings
import numpy as np
import pandas as pd
import neurokit2 as nk

warnings.filterwarnings("ignore")

# Locate target
target = None
if os.path.exists("pred_results/data_path.txt"):
    target = open("pred_results/data_path.txt").read().strip()
if not target or not os.path.exists(target):
    matches = glob.glob("/data/lab/VeriFront/**/benchmark/datasets/biosignals/bio_eventrelated_100hz.csv", recursive=True)
    target = matches[0]
print("target:", target)

data = pd.read_csv(target)
sr = 100
print("data shape:", data.shape, "duration:", len(data)/sr)

# Localize stimulus/event periods as downward Photosensor pulses (below threshold).
events = nk.events_find(
    data["Photosensor"],
    threshold_keep="below",
    event_conditions=["Negative", "Neutral", "Neutral", "Negative"]
)
print("events found:")
for k, v in events.items():
    print(k, v)

# Process multimodal biosignals.
signals, info = nk.bio_process(ecg=data["ECG"], rsp=data["RSP"], eda=data["EDA"], sampling_rate=sr)
print("processed columns count:", len(signals.columns))
print("processed columns:", signals.columns.tolist())
print("info keys:", list(info.keys()))

# Try several epoch windows to inspect returned feature columns and stability.
for end in [3, 5, 6, 8, 10]:
    print("\n=== epochs_end", end, "===")
    try:
        epochs = nk.epochs_create(signals, events, sampling_rate=sr, epochs_start=-0.1, epochs_end=end)
        results = nk.bio_analyze(epochs, sampling_rate=sr)
        print("results shape:", results.shape)
        print("columns:", results.columns.tolist())
        cols = [c for c in ["Label","Condition","Event_Onset","ECG_Rate_Mean","RSP_Rate_Mean","EDA_Peak_Amplitude","SCR_Peak_Amplitude"] if c in results.columns]
        print(results[cols].to_string(index=False))
    except Exception as e:
        print("FAILED:", repr(e))