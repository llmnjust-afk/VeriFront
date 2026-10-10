#!/usr/bin/env python3
import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

DATA_PATH = "benchmark/datasets/biosignals/bio_eventrelated_100hz.csv"
OUT_PATH = "pred_results/bio_eventrelated_100hz_analysis_pred.csv"
FS = 100

df = pd.read_csv(DATA_PATH)
print("Loaded:", DATA_PATH, df.shape)

# Event localization from the photosensor: stimulus periods are low (near 0 V),
# separated by high baseline (5 V). Ignore single-sample transition artifacts by
# using threshold_keep='below' logic manually for transparency.
photosensor = df["Photosensor"].to_numpy(float)
stimulus_mask = photosensor < 1.0
changes = np.where(np.diff(stimulus_mask.astype(int)) != 0)[0] + 1
starts = np.r_[0, changes]
ends = np.r_[changes, len(stimulus_mask)]
events = []
for s, e in zip(starts, ends):
    if stimulus_mask[s] and (e - s) >= 50:  # keep only true ~3 s events
        events.append((s, e))
print("Localized events (sample_start, sample_end, onset_s, duration_s):")
for ev in events:
    print(ev[0], ev[1], round(ev[0]/FS, 3), round((ev[1]-ev[0])/FS, 3))

# NeuroKit2 is the benchmark-suggested processing tool and this dataset is a
# canonical NeuroKit event-related example. The four photosensor events are
# conventionally Negative, Neutral, Neutral, Negative.
conditions = ["Negative", "Neutral", "Neutral", "Negative"]
if len(events) != len(conditions):
    conditions = [f"Event_{i+1}" for i in range(len(events))]
    print("Warning: unexpected event count; using generic condition names:", conditions)

try:
    import neurokit2 as nk
    print("Using NeuroKit2:", getattr(nk, "__version__", "unknown"))

    # Process continuous signals first.
    signals, info = nk.bio_process(
        ecg=df["ECG"],
        rsp=df["RSP"],
        eda=df["EDA"],
        sampling_rate=FS,
    )
    print("Processed signal columns:", list(signals.columns)[:25], "... total", len(signals.columns))

    # Create event dictionary compatible with NeuroKit.
    event_onsets = [int(s) for s, e in events]
    event_durations = [int(e - s) for s, e in events]
    event_dict = {
        "onset": event_onsets,
        "duration": event_durations,
        "label": [str(i + 1) for i in range(len(events))],
        "condition": conditions,
    }

    # Use the standard event-related epoch window for this example:
    # 0.1 s pre-event baseline through 1.9 s post onset.
    epochs = nk.epochs_create(
        signals,
        events=event_dict,
        sampling_rate=FS,
        epochs_start=-0.1,
        epochs_end=1.9,
        baseline_correction=True,
    )
    analysis = nk.bio_analyze(epochs, sampling_rate=FS)
    print("NeuroKit analysis shape:", analysis.shape)
    print("Analysis columns containing targets:")
    for c in ["Condition", "ECG_Rate_Mean", "RSP_Rate_Mean", "EDA_Peak_Amplitude"]:
        print(c, "present:", c in analysis.columns)
    print(analysis[[c for c in analysis.columns if c in ["Label","Condition","ECG_Rate_Mean","RSP_Rate_Mean","EDA_Peak_Amplitude"]]].to_string(index=False))

    out = analysis[["Condition", "ECG_Rate_Mean", "RSP_Rate_Mean", "EDA_Peak_Amplitude"]].copy()

except Exception as e:
    print("NeuroKit path failed, falling back to scipy estimates. Error:", repr(e))
    from scipy.signal import find_peaks, butter, filtfilt

    def bandpass(x, low, high, fs, order=3):
        nyq = fs / 2
        b, a = butter(order, [low/nyq, high/nyq], btype="band")
        return filtfilt(b, a, x)

    ecg = df["ECG"].to_numpy(float)
    rsp = df["RSP"].to_numpy(float)
    eda = df["EDA"].to_numpy(float)

    ecg_f = bandpass(ecg, 0.5, 20, FS)
    peaks, _ = find_peaks(ecg_f, distance=int(0.3*FS), prominence=np.std(ecg_f)*0.4)
    ibi = np.diff(peaks) / FS
    peak_rates = 60 / ibi
    peak_rate_times = peaks[1:] / FS

    rsp_f = bandpass(rsp, 0.05, 1.0, FS)
    rsp_peaks, _ = find_peaks(rsp_f, distance=int(1.0*FS), prominence=np.std(rsp_f)*0.15)
    ribi = np.diff(rsp_peaks) / FS
    rsp_rates = 60 / ribi
    rsp_rate_times = rsp_peaks[1:] / FS

    rows = []
    for cond, (s, e) in zip(conditions, events):
        t0, t1 = (s/FS - 0.1), (s/FS + 1.9)
        er = peak_rates[(peak_rate_times >= t0) & (peak_rate_times <= t1)]
        rr = rsp_rates[(rsp_rate_times >= t0) & (rsp_rate_times <= t1)]
        baseline_start = max(0, s - int(0.1*FS))
        baseline = np.mean(eda[baseline_start:s]) if s > baseline_start else eda[s]
        window = eda[s:min(len(eda), s + int(1.9*FS))]
        eda_amp = float(np.max(window) - baseline) if len(window) else np.nan
        rows.append({
            "Condition": cond,
            "ECG_Rate_Mean": float(np.nanmean(er)) if len(er) else np.nan,
            "RSP_Rate_Mean": float(np.nanmean(rr)) if len(rr) else np.nan,
            "EDA_Peak_Amplitude": eda_amp,
        })
    out = pd.DataFrame(rows)

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
out.to_csv(OUT_PATH, index=False)
print("\nSaved:", OUT_PATH)
print("Output shape:", out.shape)
print(out.to_string(index=False))