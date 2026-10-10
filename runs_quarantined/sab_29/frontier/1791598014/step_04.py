#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

signals = pd.read_csv("processed_bio_signals.csv")
events = pd.read_csv("localized_events.csv")
fs = 100

print("Loaded signals:", signals.shape)
print("Loaded events:")
print(events.to_string(index=False))

# Manual event-window summaries over the localized photosensor-low event periods.
rows_window = []
for _, ev in events.iterrows():
    start = int(ev["window_start_idx"])
    end = int(ev["window_end_idx"])
    seg = signals.iloc[start:end]
    rows_window.append({
        "Condition": f"Marker_{ev['marker_value']:g}",
        "Event_Number": int(ev["event_number"]),
        "Start": start,
        "End": end,
        "ECG_Rate_Mean": float(seg["ECG_Rate"].mean()),
        "RSP_Rate_Mean": float(seg["RSP_Rate"].mean()),
        "EDA_Peak_Amplitude_maxSCR": float(seg["SCR_Amplitude"].max()) if "SCR_Amplitude" in seg else np.nan,
        "EDA_Peak_Amplitude_sumSCR": float(seg["SCR_Amplitude"].sum()) if "SCR_Amplitude" in seg else np.nan,
        "SCR_Peaks_Count": int(seg["SCR_Peaks"].sum()) if "SCR_Peaks" in seg else -1,
        "EDA_Phasic_Max": float(seg["EDA_Phasic"].max()) if "EDA_Phasic" in seg else np.nan,
        "EDA_Clean_MaxMinusMin": float(seg["EDA_Clean"].max() - seg["EDA_Clean"].min()) if "EDA_Clean" in seg else np.nan,
    })
manual = pd.DataFrame(rows_window)
print("\nManual per localized low-window summaries:")
print(manual.to_string(index=False))

print("\nManual summaries aggregated by marker condition:")
agg = manual.groupby("Condition", as_index=False).agg({
    "ECG_Rate_Mean": "mean",
    "RSP_Rate_Mean": "mean",
    "EDA_Peak_Amplitude_maxSCR": "mean",
    "EDA_Peak_Amplitude_sumSCR": "mean",
    "SCR_Peaks_Count": "sum",
    "EDA_Phasic_Max": "mean",
    "EDA_Clean_MaxMinusMin": "mean",
})
print(agg.to_string(index=False))

# Try NeuroKit event-related pipeline over onset-to-end event periods.
try:
    import neurokit2 as nk
    onsets = events["window_start_idx"].astype(int).tolist()
    durations = (events["window_end_idx"] - events["window_start_idx"]).astype(int).tolist()
    labels = [f"Event_{int(n)}" for n in events["event_number"]]
    conditions = [f"Marker_{v:g}" for v in events["marker_value"]]
    nk_events = nk.events_create(event_onsets=onsets, event_durations=durations, event_labels=labels, event_conditions=conditions)
    print("\nNK events dict:", nk_events)
    epochs = nk.epochs_create(signals, events=nk_events, sampling_rate=fs, epochs_start=0, epochs_end=None, baseline_correction=False)
    features = nk.bio_analyze(epochs, sampling_rate=fs)
    print("\nNeuroKit bio_analyze event-related features columns:")
    print(features.columns.tolist())
    print(features.to_string())
    features.to_csv("nk_event_features.csv", index=False)
    print("Saved nk_event_features.csv")
except Exception as e:
    print("NeuroKit event analysis failed:", repr(e))

# Inspect SCR peak indices and amplitudes around events
scr_peaks_idx = np.where(signals["SCR_Peaks"].to_numpy() == 1)[0] if "SCR_Peaks" in signals else np.array([])
print("\nSCR peaks total:", len(scr_peaks_idx))
if len(scr_peaks_idx):
    scr_table = pd.DataFrame({
        "idx": scr_peaks_idx,
        "time_s": scr_peaks_idx / fs,
        "amplitude": signals.loc[scr_peaks_idx, "SCR_Amplitude"].to_numpy(),
        "height": signals.loc[scr_peaks_idx, "SCR_Height"].to_numpy() if "SCR_Height" in signals else np.nan,
        "eda_phasic": signals.loc[scr_peaks_idx, "EDA_Phasic"].to_numpy() if "EDA_Phasic" in signals else np.nan,
    })
    print(scr_table.to_string(index=False))
    for _, ev in events.iterrows():
        onset = int(ev["window_start_idx"])
        end = int(ev["window_end_idx"])
        post_end = min(len(signals), onset + int(10*fs))
        nearby = scr_table[(scr_table["idx"] >= onset) & (scr_table["idx"] < post_end)].copy()
        print(f"\nSCR peaks within 10s after event {int(ev['event_number'])} marker {ev['marker_value']} onset {onset}:")
        print(nearby.to_string(index=False) if len(nearby) else "None")