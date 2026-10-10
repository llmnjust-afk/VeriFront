#!/usr/bin/env python3
import os
import sys
import importlib.util
import pandas as pd
import numpy as np

with open("dataset_path.txt") as f:
    path = f.read().strip()
df = pd.read_csv(path)
fs = 100

print("Dataset:", path, "shape", df.shape)

# Check available processing libraries
for pkg in ["neurokit2", "scipy", "sklearn"]:
    print(pkg, "available:", importlib.util.find_spec(pkg) is not None)

# Localize event periods from photosensor: the ~3 s low pulses following marker-coded one-sample values.
photo = np.round(df["Photosensor"].to_numpy(), 6)
change_idx = np.where(np.diff(photo) != 0)[0] + 1
starts = np.r_[0, change_idx]
ends = np.r_[change_idx, len(photo)]
runs = pd.DataFrame({"start_idx": starts, "end_idx": ends, "value": photo[starts], "duration_s": (ends-starts)/fs})
print("Runs:")
print(runs.to_string(index=False))

events = []
for i in range(1, len(runs)-1):
    # coded marker is a one sample non-baseline non-zero run followed by near-zero event window
    if runs.loc[i, "duration_s"] <= 0.02 and runs.loc[i, "value"] not in [5.0, 0.0] and runs.loc[i+1, "value"] == 0.0:
        events.append({
            "event_number": len(events)+1,
            "marker_value": runs.loc[i, "value"],
            "onset_idx": int(runs.loc[i, "start_idx"]),
            "window_start_idx": int(runs.loc[i+1, "start_idx"]),
            "window_end_idx": int(runs.loc[i+1, "end_idx"]),
            "duration_s": float(runs.loc[i+1, "duration_s"]),
        })
events = pd.DataFrame(events)
print("Localized events:")
print(events.to_string(index=False))

# Use NeuroKit2 when available for robust event-related processing.
try:
    import neurokit2 as nk
    print("NeuroKit2 version:", getattr(nk, "__version__", "unknown"))
    signals, info = nk.bio_process(ecg=df["ECG"], rsp=df["RSP"], eda=df["EDA"], sampling_rate=fs)
    print("Processed signal columns:", signals.columns.tolist())
    print("Info keys:", list(info.keys()))
    print("Signals head:")
    print(signals.head().to_string(index=False))
    print("Signals describe subset:")
    cols = [c for c in ["ECG_Rate", "RSP_Rate", "EDA_Phasic", "SCR_Amplitude", "SCR_Peaks"] if c in signals.columns]
    print(signals[cols].describe().T.to_string())
except Exception as e:
    print("NeuroKit2 processing failed:", repr(e))
    # Fallback rough processing using scipy
    from scipy.signal import find_peaks, butter, filtfilt
    signals = pd.DataFrame(index=df.index)
    b, a = butter(2, [0.5/(fs/2), 25/(fs/2)], btype="band")
    ecg_clean = filtfilt(b, a, df["ECG"].to_numpy())
    peaks, _ = find_peaks(ecg_clean, distance=int(0.35*fs), prominence=np.std(ecg_clean)*0.5)
    ecg_rate = np.full(len(df), np.nan)
    if len(peaks) > 1:
        rr = np.diff(peaks)/fs
        bpm = 60/rr
        mid = ((peaks[:-1]+peaks[1:])//2).astype(int)
        ecg_rate[:] = np.interp(np.arange(len(df)), mid, bpm, left=bpm[0], right=bpm[-1])
    signals["ECG_Rate"] = ecg_rate
    b, a = butter(2, [0.05/(fs/2), 1.0/(fs/2)], btype="band")
    rsp_clean = filtfilt(b, a, df["RSP"].to_numpy())
    rpeaks, _ = find_peaks(rsp_clean, distance=int(1.5*fs), prominence=np.std(rsp_clean)*0.2)
    rsp_rate = np.full(len(df), np.nan)
    if len(rpeaks) > 1:
        intervals = np.diff(rpeaks)/fs
        rpm = 60/intervals
        mid = ((rpeaks[:-1]+rpeaks[1:])//2).astype(int)
        rsp_rate[:] = np.interp(np.arange(len(df)), mid, rpm, left=rpm[0], right=rpm[-1])
    signals["RSP_Rate"] = rsp_rate
    signals["EDA_Phasic"] = df["EDA"] - pd.Series(df["EDA"]).rolling(fs*4, center=True, min_periods=1).median()
    eda_peaks, props = find_peaks(signals["EDA_Phasic"], distance=fs, prominence=0.01)
    amp = np.zeros(len(df))
    amp[eda_peaks] = props.get("prominences", np.zeros(len(eda_peaks)))
    signals["SCR_Amplitude"] = amp
    signals["SCR_Peaks"] = 0
    signals.loc[eda_peaks, "SCR_Peaks"] = 1
    print("Fallback processed columns:", signals.columns.tolist())

# Save processed signals and events for next turn
signals.to_csv("processed_bio_signals.csv", index=False)
events.to_csv("localized_events.csv", index=False)
print("Saved processed_bio_signals.csv and localized_events.csv")