#!/usr/bin/env python3
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import neurokit2 as nk
from scipy import signal

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)

SAMPLING_RATE = 100
data_path = Path("biosignals/bio_resting_5min_100hz.csv")
if not data_path.exists():
    alt = Path("benchmark/datasets/biosignals/bio_resting_5min_100hz.csv")
    if alt.exists():
        data_path = alt
    else:
        raise FileNotFoundError("Could not find bio_resting_5min_100hz.csv")

print("Reading:", data_path)
df = pd.read_csv(data_path)
print("Data shape:", df.shape)
print("Columns:", list(df.columns))

ecg = pd.to_numeric(df["ECG"], errors="coerce").to_numpy(dtype=float)
if np.isnan(ecg).any():
    n_nan = int(np.isnan(ecg).sum())
    print("Interpolating ECG NaNs:", n_nan)
    ecg = pd.Series(ecg).interpolate(limit_direction="both").to_numpy(dtype=float)

duration_s = len(ecg) / SAMPLING_RATE
print(f"ECG samples: {len(ecg)}, duration: {duration_s:.2f} s")

# Clean ECG and detect R-peaks. NeuroKit's detector is used, with artifact correction enabled.
ecg_cleaned = nk.ecg_clean(ecg, sampling_rate=SAMPLING_RATE, method="neurokit")
signals, info = nk.ecg_peaks(
    ecg_cleaned,
    sampling_rate=SAMPLING_RATE,
    method="neurokit",
    correct_artifacts=True,
)
rpeaks = np.asarray(info["ECG_R_Peaks"], dtype=int)
rpeaks = rpeaks[(rpeaks >= 0) & (rpeaks < len(ecg))]
rpeaks = np.unique(rpeaks)

# Fallback if the primary detector fails implausibly.
if len(rpeaks) < 20:
    print("Primary ECG detector found too few peaks; trying scipy fallback.")
    # Bandpass for QRS range, then find prominent positive deflections.
    sos = signal.butter(3, [5, 20], btype="bandpass", fs=SAMPLING_RATE, output="sos")
    filt = signal.sosfiltfilt(sos, ecg)
    min_dist = int(0.35 * SAMPLING_RATE)
    prom = max(0.15 * np.nanstd(filt), 1e-6)
    peaks, props = signal.find_peaks(filt, distance=min_dist, prominence=prom)
    rpeaks = peaks.astype(int)
    info = {"ECG_R_Peaks": rpeaks}
    print("Fallback peaks:", len(rpeaks))

rr_ms = np.diff(rpeaks) / SAMPLING_RATE * 1000.0
mean_hr = 60000.0 / np.mean(rr_ms) if len(rr_ms) else np.nan
print("Detected R-peaks:", len(rpeaks))
print(f"Mean RR: {np.mean(rr_ms):.3f} ms; SD RR: {np.std(rr_ms, ddof=1):.3f} ms; mean HR: {mean_hr:.3f} bpm")
print("First 10 R-peak sample indices:", rpeaks[:10].tolist())
print("First 10 RR intervals (ms):", np.round(rr_ms[:10], 3).tolist())

# Compute HRV indices by domain.
# NeuroKit returns one-row dataframes with standard HRV_* feature names.
peaks_dict = {"ECG_R_Peaks": rpeaks}

domain_frames = []
domain_counts = {}
for domain_name, func in [
    ("time", nk.hrv_time),
    ("frequency", nk.hrv_frequency),
    ("nonlinear", nk.hrv_nonlinear),
]:
    try:
        feat = func(peaks_dict, sampling_rate=SAMPLING_RATE, show=False)
    except TypeError:
        feat = func(peaks_dict, sampling_rate=SAMPLING_RATE)
    feat = feat.reset_index(drop=True)
    domain_frames.append(feat)
    domain_counts[domain_name] = feat.shape[1]
    print(f"{domain_name} features: {feat.shape[1]}")
    print(" ", list(feat.columns)[:12], "..." if feat.shape[1] > 12 else "")

features = pd.concat(domain_frames, axis=1)

# Add a small amount of transparent peak-detection metadata; the HRV_* columns are the requested features.
metadata = pd.DataFrame(
    {
        "Sampling_Rate": [SAMPLING_RATE],
        "ECG_Length_Samples": [len(ecg)],
        "ECG_Duration_Seconds": [duration_s],
        "ECG_R_Peaks_N": [len(rpeaks)],
        "ECG_RR_Intervals_N": [len(rr_ms)],
        "ECG_Mean_HR_BPM_From_RR": [mean_hr],
    }
)
out = pd.concat([metadata, features], axis=1)

# Ensure numeric finite/NaN CSV-safe values and stable column order.
out = out.apply(pd.to_numeric, errors="coerce")

out_dir = Path("pred_results")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "hrv_analysis_pred.csv"
out.to_csv(out_path, index=False)

print("Saved:", out_path)
print("Output shape:", out.shape)
print("Domain feature counts:", domain_counts)
print("Output columns:")
print(list(out.columns))
print("Output preview:")
print(out.to_string(index=False))