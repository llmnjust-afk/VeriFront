#!/usr/bin/env python3
"""
RRV analysis for biosignals/bio_eventrelated_100hz.csv.

This script:
1. Locates and loads the event-related biosignal CSV.
2. Cleans the RSP signal.
3. Extracts inhalation-related extrema and a respiratory-rate signal.
4. Computes RRV indices spanning time, frequency, and nonlinear domains.
5. Saves a one-row feature table to pred_results/rrv_analysis_pred.csv.
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from scipy import signal
import neurokit2 as nk

warnings.filterwarnings("ignore", category=RuntimeWarning)

FS = 100
OUTDIR = Path("pred_results")
OUTDIR.mkdir(exist_ok=True)
OUTFILE = OUTDIR / "rrv_analysis_pred.csv"


def find_input_file():
    candidates = [
        Path("biosignals/bio_eventrelated_100hz.csv"),
        Path("benchmark/datasets/biosignals/bio_eventrelated_100hz.csv"),
    ]
    path_file = OUTDIR / "data_path.txt"
    if path_file.exists():
        candidates.insert(0, Path(path_file.read_text().strip()))
    for c in candidates:
        if c.exists():
            return c.resolve()

    roots = [Path("."), Path(".."), Path("../.."), Path("/data/lab")]
    seen = set()
    for root in roots:
        try:
            rr = root.resolve()
            if rr in seen:
                continue
            seen.add(rr)
            matches = list(root.rglob("bio_eventrelated_100hz.csv"))
            if matches:
                return matches[0].resolve()
        except Exception:
            pass
    raise FileNotFoundError("Could not locate bio_eventrelated_100hz.csv")


def flatten_features(prefix, df):
    """Convert a one-row DataFrame to a prefixed feature dict."""
    out = {}
    if df is None or len(df) == 0:
        return out
    row = df.iloc[0]
    for k, v in row.items():
        try:
            out[f"{prefix}{k}"] = float(v) if pd.notna(v) else np.nan
        except Exception:
            out[f"{prefix}{k}"] = v
    return out


def safe_nk_feature(func, indices, prefix):
    """Compute NeuroKit feature table safely and prefix column names."""
    try:
        table = func(indices, sampling_rate=FS, show=False)
        return flatten_features(prefix, table)
    except Exception as e:
        print(f"{func.__name__} failed for {prefix}: {repr(e)}")
        return {}


def summarize_intervals(name, indices):
    """Summarize breath-to-breath intervals from extrema indices."""
    feats = {}
    indices = np.asarray(indices, dtype=int)
    if len(indices) >= 2:
        intervals_s = np.diff(indices) / FS
        intervals_ms = intervals_s * 1000
        diffs_ms = np.diff(intervals_ms)
        feats[f"{name}_Interval_Count"] = len(intervals_ms)
        feats[f"{name}_Interval_Mean_ms"] = float(np.mean(intervals_ms))
        feats[f"{name}_Interval_SD_ms"] = float(np.std(intervals_ms, ddof=1)) if len(intervals_ms) > 1 else np.nan
        feats[f"{name}_Interval_Median_ms"] = float(np.median(intervals_ms))
        feats[f"{name}_Interval_Min_ms"] = float(np.min(intervals_ms))
        feats[f"{name}_Interval_Max_ms"] = float(np.max(intervals_ms))
        feats[f"{name}_Interval_RMSSD_ms"] = float(np.sqrt(np.mean(diffs_ms**2))) if len(diffs_ms) else np.nan
        feats[f"{name}_Rate_Mean_bpm_from_intervals"] = float(np.mean(60 / intervals_s))
        feats[f"{name}_Rate_SD_bpm_from_intervals"] = float(np.std(60 / intervals_s, ddof=1)) if len(intervals_s) > 1 else np.nan
    else:
        feats[f"{name}_Interval_Count"] = 0
    return feats


# Load data
data_path = find_input_file()
df = pd.read_csv(data_path)
rsp = df["RSP"].astype(float).to_numpy()
duration_s = len(rsp) / FS

print("Input file:", data_path)
print("Loaded data shape:", df.shape)
print("RSP duration_s:", duration_s)

# Clean RSP and extract extrema
rsp_clean = nk.rsp_clean(rsp, sampling_rate=FS, method="khodadad2018")
peak_signals, peak_info = nk.rsp_peaks(rsp_clean, sampling_rate=FS, method="khodadad2018")

# NeuroKit labels maxima as RSP_Peaks and minima as RSP_Troughs. In many belts,
# maxima correspond to inspiration/inhalation peaks; troughs are inhalation onsets.
rsp_inhalation_peaks = np.asarray(peak_info.get("RSP_Peaks", []), dtype=int)
rsp_inhalation_onsets = np.asarray(peak_info.get("RSP_Troughs", []), dtype=int)

# Respiratory-rate signal from inhalation onsets/troughs
rsp_rate = nk.rsp_rate(
    rsp_clean,
    troughs=rsp_inhalation_onsets,
    sampling_rate=FS,
    method="trough",
    interpolation_method="monotone_cubic",
)
rsp_rate = np.asarray(rsp_rate, dtype=float)

# Peaks of the respiratory-rate signal (local rate maxima)
finite_rate = np.nan_to_num(rsp_rate, nan=np.nanmedian(rsp_rate))
min_distance = int(max(1, FS * 2.0))
prominence = max(0.01, 0.10 * np.nanstd(finite_rate))
rate_peak_idx, rate_peak_props = signal.find_peaks(
    finite_rate,
    distance=min_distance,
    prominence=prominence,
)

print("Cleaned RSP mean/std:", float(np.mean(rsp_clean)), float(np.std(rsp_clean)))
print("RSP inhalation peaks detected:", len(rsp_inhalation_peaks))
print("RSP inhalation onsets/troughs detected:", len(rsp_inhalation_onsets))
print("Respiratory rate mean/std bpm:", float(np.nanmean(rsp_rate)), float(np.nanstd(rsp_rate)))
print("Respiratory-rate peaks detected:", len(rate_peak_idx))
print("First 10 RSP peak times_s:", np.round(rsp_inhalation_peaks[:10] / FS, 3).tolist())
print("First 10 RSP onset/trough times_s:", np.round(rsp_inhalation_onsets[:10] / FS, 3).tolist())
print("First 10 rate peak times_s:", np.round(rate_peak_idx[:10] / FS, 3).tolist())

# Standard NeuroKit interval-related RRV/RSP metrics
try:
    processed, proc_info = nk.rsp_process(rsp, sampling_rate=FS, method="khodadad2018")
    interval_rrv = nk.rsp_intervalrelated(processed, sampling_rate=FS)
    print("nk.rsp_intervalrelated computed columns:", len(interval_rrv.columns))
except Exception as e:
    print("nk.rsp_intervalrelated failed:", repr(e))
    interval_rrv = pd.DataFrame()

features = {
    "Sampling_Rate_Hz": FS,
    "N_Samples": len(rsp),
    "Duration_s": duration_s,
    "RSP_Raw_Mean": float(np.mean(rsp)),
    "RSP_Raw_SD": float(np.std(rsp, ddof=1)),
    "RSP_Clean_Mean": float(np.mean(rsp_clean)),
    "RSP_Clean_SD": float(np.std(rsp_clean, ddof=1)),
    "RSP_Inhalation_Peaks_N": int(len(rsp_inhalation_peaks)),
    "RSP_Inhalation_Onsets_Troughs_N": int(len(rsp_inhalation_onsets)),
    "RSP_Rate_Signal_Mean_bpm": float(np.nanmean(rsp_rate)),
    "RSP_Rate_Signal_SD_bpm": float(np.nanstd(rsp_rate, ddof=1)),
    "RSP_Rate_Signal_Median_bpm": float(np.nanmedian(rsp_rate)),
    "RSP_Rate_Signal_Min_bpm": float(np.nanmin(rsp_rate)),
    "RSP_Rate_Signal_Max_bpm": float(np.nanmax(rsp_rate)),
    "RSP_Rate_Peaks_N": int(len(rate_peak_idx)),
    "RSP_Rate_Peaks_Mean_bpm": float(np.mean(finite_rate[rate_peak_idx])) if len(rate_peak_idx) else np.nan,
    "RSP_Rate_Peaks_SD_bpm": float(np.std(finite_rate[rate_peak_idx], ddof=1)) if len(rate_peak_idx) > 1 else np.nan,
}

# Add built-in RRV interval features without extra prefix because they already use RRV/RSP names
features.update(flatten_features("", interval_rrv))

# Add explicit interval summaries
features.update(summarize_intervals("RSP_Inhalation_Peak", rsp_inhalation_peaks))
features.update(summarize_intervals("RSP_Inhalation_Onset", rsp_inhalation_onsets))
features.update(summarize_intervals("RSP_Rate_Peak", rate_peak_idx))

# Add HRV-style time/frequency/nonlinear RRV on inhalation peaks and onsets
features.update(safe_nk_feature(nk.hrv_time, rsp_inhalation_peaks, "RRV_InhalationPeak_Time_"))
features.update(safe_nk_feature(nk.hrv_frequency, rsp_inhalation_peaks, "RRV_InhalationPeak_Frequency_"))
features.update(safe_nk_feature(nk.hrv_nonlinear, rsp_inhalation_peaks, "RRV_InhalationPeak_Nonlinear_"))

features.update(safe_nk_feature(nk.hrv_time, rsp_inhalation_onsets, "RRV_InhalationOnset_Time_"))
features.update(safe_nk_feature(nk.hrv_frequency, rsp_inhalation_onsets, "RRV_InhalationOnset_Frequency_"))
features.update(safe_nk_feature(nk.hrv_nonlinear, rsp_inhalation_onsets, "RRV_InhalationOnset_Nonlinear_"))

# Save result CSV
result = pd.DataFrame([features])

# Stable column ordering: metadata first, then alphabetical remaining
front = [
    "Sampling_Rate_Hz", "N_Samples", "Duration_s",
    "RSP_Inhalation_Peaks_N", "RSP_Inhalation_Onsets_Troughs_N", "RSP_Rate_Peaks_N",
    "RSP_Rate_Signal_Mean_bpm", "RSP_Rate_Signal_SD_bpm",
]
cols = [c for c in front if c in result.columns] + sorted([c for c in result.columns if c not in front])
result = result[cols]
result.to_csv(OUTFILE, index=False)

# Also save processed signal table for traceability
debug = pd.DataFrame({
    "RSP_Raw": rsp,
    "RSP_Clean": rsp_clean,
    "RSP_Rate_bpm": rsp_rate,
    "RSP_Inhalation_Peak": peak_signals["RSP_Peaks"].to_numpy() if "RSP_Peaks" in peak_signals else 0,
    "RSP_Inhalation_Onset_Trough": peak_signals["RSP_Troughs"].to_numpy() if "RSP_Troughs" in peak_signals else 0,
})
rate_peak_marker = np.zeros(len(debug), dtype=int)
rate_peak_marker[rate_peak_idx] = 1
debug["RSP_Rate_Peak"] = rate_peak_marker
debug.to_csv(OUTDIR / "rrv_processed_signals.csv", index=False)

print("Saved main RRV analysis to:", OUTFILE)
print("Saved processed signals to:", OUTDIR / "rrv_processed_signals.csv")
print("Result shape:", result.shape)
print("First 40 output columns:", list(result.columns[:40]))
print("Selected key values:")
for k in [
    "RSP_Rate_Mean",
    "RRV_RMSSD",
    "RRV_MeanBB",
    "RRV_SDBB",
    "RRV_LF",
    "RRV_HF",
    "RRV_LFHF",
    "RRV_SD1",
    "RRV_SD2",
    "RRV_SampEn",
]:
    if k in result.columns:
        print(f"  {k}: {result.loc[0, k]}")