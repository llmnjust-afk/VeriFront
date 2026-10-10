#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

signals = pd.read_csv("processed_bio_signals.csv")
events = pd.read_csv("localized_events.csv")
fs = 100

print("Preparing final analysis. Signals:", signals.shape, "Events:", len(events))

# Try NeuroKit event-related extraction over a physiologically plausible 10 s post-event epoch
# (EDA/SCR responses often peak several seconds after event onset).
try:
    import neurokit2 as nk
    onsets = events["window_start_idx"].astype(int).tolist()
    labels = [f"Event_{int(n)}" for n in events["event_number"]]
    conditions = [f"Marker_{v:g}" for v in events["marker_value"]]
    nk_events = nk.events_create(
        event_onsets=onsets,
        event_durations=[int(3*fs)] * len(onsets),
        event_labels=labels,
        event_conditions=conditions
    )
    epochs = nk.epochs_create(
        signals,
        events=nk_events,
        sampling_rate=fs,
        epochs_start=0,
        epochs_end=10,
        baseline_correction=False
    )
    features = nk.bio_analyze(epochs, sampling_rate=fs)
    print("NeuroKit features columns:")
    print(features.columns.tolist())
    print(features.to_string())
    features.to_csv("nk_event_features_10s.csv", index=False)
    print("Saved nk_event_features_10s.csv")
except Exception as e:
    print("NeuroKit event feature extraction failed:", repr(e))
    features = None

# Build final required table.
# We use localized photosensor events as conditions/events. Heart and respiratory rates are
# averaged over the visible stimulus period (~3 s photosensor-low window). For EDA, because SCR
# has a delayed latency, we use the maximum SCR_Amplitude in the 0-10 s post-event epoch.
rows = []
for _, ev in events.iterrows():
    onset = int(ev["window_start_idx"])
    stim_end = int(ev["window_end_idx"])
    eda_end = min(len(signals), onset + int(10 * fs))
    stim = signals.iloc[onset:stim_end]
    post = signals.iloc[onset:eda_end]
    
    if "SCR_Amplitude" in post.columns:
        eda_amp = float(np.nanmax(post["SCR_Amplitude"].to_numpy()))
    elif "EDA_Phasic" in post.columns:
        eda_amp = float(np.nanmax(post["EDA_Phasic"].to_numpy()))
    else:
        eda_amp = float(np.nanmax(post["EDA_Clean"].to_numpy()) - np.nanmin(post["EDA_Clean"].to_numpy()))
    
    rows.append({
        "Condition": f"Event_{int(ev['event_number'])}_Marker_{ev['marker_value']:g}",
        "ECG_Rate_Mean": float(np.nanmean(stim["ECG_Rate"].to_numpy())),
        "RSP_Rate_Mean": float(np.nanmean(stim["RSP_Rate"].to_numpy())),
        "EDA_Peak_Amplitude": eda_amp,
    })

final = pd.DataFrame(rows, columns=["Condition", "ECG_Rate_Mean", "RSP_Rate_Mean", "EDA_Peak_Amplitude"])

# Also make a condition-aggregated diagnostic table, but final submission remains event-localized.
agg = final.assign(Marker=events["marker_value"].map(lambda v: f"Marker_{v:g}")).groupby("Marker", as_index=False).agg({
    "ECG_Rate_Mean": "mean",
    "RSP_Rate_Mean": "mean",
    "EDA_Peak_Amplitude": "mean",
})
print("\nFinal event-localized required table:")
print(final.to_string(index=False))
print("\nDiagnostic aggregation by repeated marker value:")
print(agg.to_string(index=False))

os.makedirs("pred_results", exist_ok=True)
out = "pred_results/bio_eventrelated_100hz_analysis_pred.csv"
final.to_csv(out, index=False)
print("\nSaved:", out)
print("Read-back:")
print(pd.read_csv(out).to_string(index=False))