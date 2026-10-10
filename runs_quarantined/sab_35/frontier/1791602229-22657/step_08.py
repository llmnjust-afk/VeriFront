#!/usr/bin/env python3
import os
import warnings
import numpy as np
import pandas as pd
import neurokit2 as nk
from scipy.signal import find_peaks

warnings.filterwarnings("ignore")

DATA_PATH = "benchmark/datasets/biosignals/bio_eventrelated_100hz.csv"
OUT_PATH = "pred_results/rrv_analysis_pred.csv"
FS = 100

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

print("Loading:", DATA_PATH)
df = pd.read_csv(DATA_PATH)
rsp = pd.to_numeric(df["RSP"], errors="coerce").to_numpy(dtype=float)

# Fill any unexpected missing values by interpolation to make processing robust.
if not np.all(np.isfinite(rsp)):
    s = pd.Series(rsp).interpolate(limit_direction="both")
    rsp = s.to_numpy(dtype=float)

print("Samples:", len(rsp), "Sampling rate:", FS, "Duration_s:", len(rsp) / FS)

# Clean RSP and extract respiration landmarks and respiratory rate.
signals, info = nk.rsp_process(rsp, sampling_rate=FS, method="khodadad2018")
clean = signals["RSP_Clean"].to_numpy(dtype=float)
rsp_rate = signals["RSP_Rate"].to_numpy(dtype=float)

# NeuroKit labels RSP_Troughs as inhalation onsets; these are the breath timing events for RRV.
inhalation_idx = np.asarray(info["RSP_Troughs"], dtype=int)
exhalation_idx = np.asarray(info["RSP_Peaks"], dtype=int)

# Peaks of the respiratory-rate signal itself (local maxima in instantaneous breaths/min).
min_distance = int(1.0 * FS)
rr_prom = max(0.01, 0.05 * np.nanstd(rsp_rate))
rate_peak_idx, rate_peak_props = find_peaks(rsp_rate, distance=min_distance, prominence=rr_prom)

print("Detected inhalation events (RSP_Troughs):", len(inhalation_idx), inhalation_idx[:12])
print("Detected exhalation events (RSP_Peaks):", len(exhalation_idx), exhalation_idx[:12])
print("Detected respiratory-rate local maxima:", len(rate_peak_idx), rate_peak_idx[:12])

# Main RRV output from NeuroKit2: time-domain, frequency-domain, and nonlinear indices.
rrv = nk.rsp_rrv(signals, sampling_rate=FS, show=False, silent=True).reset_index(drop=True)
print("nk.rsp_rrv columns:", list(rrv.columns))
print(rrv.T.to_string())

# Additional interval-related features provided by NeuroKit2 (includes mean respiratory rate,
# amplitude and symmetry descriptors plus RRV indices). Merge without duplicating columns.
try:
    interval = nk.rsp_intervalrelated(signals, sampling_rate=FS).reset_index(drop=True)
    print("nk.rsp_intervalrelated columns:", list(interval.columns))
except Exception as e:
    print("rsp_intervalrelated failed; continuing with rsp_rrv only:", repr(e))
    interval = pd.DataFrame(index=[0])

# Manual feature additions for traceability of cleaned signal and extracted peaks.
breath_intervals_s = np.diff(inhalation_idx) / FS
breath_intervals_ms = breath_intervals_s * 1000.0

manual = {
    "Sampling_Rate_Hz": FS,
    "Duration_s": len(rsp) / FS,
    "RSP_Raw_Mean": float(np.nanmean(rsp)),
    "RSP_Raw_SD": float(np.nanstd(rsp, ddof=1)),
    "RSP_Clean_Mean": float(np.nanmean(clean)),
    "RSP_Clean_SD": float(np.nanstd(clean, ddof=1)),
    "RSP_Clean_Min": float(np.nanmin(clean)),
    "RSP_Clean_Max": float(np.nanmax(clean)),
    "RSP_Inhalation_Peaks_N": int(len(inhalation_idx)),
    "RSP_Exhalation_Peaks_N": int(len(exhalation_idx)),
    "RSP_Inhalation_Peaks_Indices": ";".join(map(str, inhalation_idx.tolist())),
    "RSP_Exhalation_Peaks_Indices": ";".join(map(str, exhalation_idx.tolist())),
    "RSP_Rate_Mean_Manual": float(np.nanmean(rsp_rate)),
    "RSP_Rate_SD_Manual": float(np.nanstd(rsp_rate, ddof=1)),
    "RSP_Rate_Min": float(np.nanmin(rsp_rate)),
    "RSP_Rate_Max": float(np.nanmax(rsp_rate)),
    "RSP_Rate_Peaks_N": int(len(rate_peak_idx)),
    "RSP_Rate_Peaks_Indices": ";".join(map(str, rate_peak_idx.tolist())),
    "RSP_Rate_Peaks_Values": ";".join(f"{x:.6g}" for x in rsp_rate[rate_peak_idx].tolist()),
}

if len(breath_intervals_s) > 0:
    manual.update({
        "Breath_Interval_Mean_s": float(np.nanmean(breath_intervals_s)),
        "Breath_Interval_SD_s": float(np.nanstd(breath_intervals_s, ddof=1)) if len(breath_intervals_s) > 1 else np.nan,
        "Breath_Interval_Min_s": float(np.nanmin(breath_intervals_s)),
        "Breath_Interval_Max_s": float(np.nanmax(breath_intervals_s)),
        "Breath_Interval_Median_s": float(np.nanmedian(breath_intervals_s)),
        "Breath_Intervals_ms": ";".join(f"{x:.6g}" for x in breath_intervals_ms.tolist()),
    })
else:
    manual.update({
        "Breath_Interval_Mean_s": np.nan,
        "Breath_Interval_SD_s": np.nan,
        "Breath_Interval_Min_s": np.nan,
        "Breath_Interval_Max_s": np.nan,
        "Breath_Interval_Median_s": np.nan,
        "Breath_Intervals_ms": "",
    })

manual_df = pd.DataFrame([manual])

# Combine in a stable order: manual traceability, interval descriptors, then full RRV indices.
result = manual_df.copy()
for source in [interval, rrv]:
    for col in source.columns:
        if col not in result.columns:
            result[col] = source.loc[0, col]

# Replace infinities with NaN, leave list columns as strings.
for col in result.columns:
    if pd.api.types.is_numeric_dtype(result[col]):
        result[col] = result[col].replace([np.inf, -np.inf], np.nan)

result.to_csv(OUT_PATH, index=False)
print("Saved:", OUT_PATH)
print("Output shape:", result.shape)
print("Output columns:")
for c in result.columns:
    print(" ", c)
print("Output preview:")
print(result.T.to_string())