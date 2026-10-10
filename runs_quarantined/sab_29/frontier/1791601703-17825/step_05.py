#!/usr/bin/env python3
import os, glob, warnings
import numpy as np
import pandas as pd
import neurokit2 as nk

warnings.filterwarnings("ignore")

# Locate dataset
target = None
if os.path.exists("pred_results/data_path.txt"):
    target = open("pred_results/data_path.txt").read().strip()
if not target or not os.path.exists(target):
    matches = glob.glob("/data/lab/VeriFront/**/benchmark/datasets/biosignals/bio_eventrelated_100hz.csv", recursive=True)
    if not matches:
        raise FileNotFoundError("bio_eventrelated_100hz.csv not found")
    target = matches[0]

sampling_rate = 100
data = pd.read_csv(target)
print("Using:", target)
print("Data shape:", data.shape)

# Event localization from the photosensor: event stimuli are low pulses.
conditions = ["Negative", "Neutral", "Neutral", "Negative"]
events = nk.events_find(
    data["Photosensor"],
    threshold_keep="below",
    event_conditions=conditions
)
print("Localized events:")
print(pd.DataFrame(events).to_string(index=False))

# Biosignal processing
signals, info = nk.bio_process(
    ecg=data["ECG"],
    rsp=data["RSP"],
    eda=data["EDA"],
    sampling_rate=sampling_rate
)

# Use an event-related epoch that includes a short pre-stimulus baseline and
# the full photosensor pulse (about 3 s post-onset).
epochs = nk.epochs_create(
    signals,
    events,
    sampling_rate=sampling_rate,
    epochs_start=-0.1,
    epochs_end=3.0
)
features = nk.bio_analyze(epochs, sampling_rate=sampling_rate)

# Required prediction table: one event-related feature row per localized event.
required = ["Condition", "ECG_Rate_Mean", "RSP_Rate_Mean", "EDA_Peak_Amplitude"]
out = features[required].copy()

os.makedirs("pred_results", exist_ok=True)
out_path = "pred_results/bio_eventrelated_100hz_analysis_pred.csv"
out.to_csv(out_path, index=False)

print("\nFeature table:")
print(out.to_string(index=False))
print("\nAlso condition-level means for reference:")
print(out.groupby("Condition", as_index=False)[required[1:]].mean().to_string(index=False))
print("\nSaved:", out_path)