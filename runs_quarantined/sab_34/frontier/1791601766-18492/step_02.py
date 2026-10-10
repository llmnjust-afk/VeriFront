#!/usr/bin/env python3
"""
Compute HRV indices from bio_resting_5min_100hz.csv and save:
pred_results/hrv_analysis_pred.csv

This version searches the working tree for the input CSV if the documented path
is not present, then computes HRV features using NeuroKit2 if available, with a
SciPy/NumPy fallback.
"""

import os
import glob
import warnings
import traceback
import numpy as np
import pandas as pd

DOCUMENTED_INPUT_PATH = "biosignals/bio_resting_5min_100hz.csv"
OUTPUT_PATH = "pred_results/hrv_analysis_pred.csv"
FS = 100


def find_input_file():
    print(f"Current working directory: {os.getcwd()}")
    print("Top-level entries:")
    try:
        print(sorted(os.listdir("."))[:100])
    except Exception as e:
        print(f"Could not list cwd: {e}")

    candidates = []
    if os.path.exists(DOCUMENTED_INPUT_PATH):
        candidates.append(DOCUMENTED_INPUT_PATH)

    patterns = [
        "**/bio_resting_5min_100hz.csv",
        "../**/bio_resting_5min_100hz.csv",
        "/data/lab/**/bio_resting_5min_100hz.csv",
        "/mnt/data/**/bio_resting_5min_100hz.csv",
    ]
    for pat in patterns:
        try:
            matches = glob.glob(pat, recursive=True)
            candidates.extend(matches)
        except Exception as e:
            print(f"Glob failed for {pat}: {e}")

    # Remove duplicates while preserving order.
    seen = set()
    uniq = []
    for c in candidates:
        ab = os.path.abspath(c)
        if ab not in seen and os.path.isfile(c):
            seen.add(ab)
            uniq.append(c)

    print(f"Candidate input files found: {uniq[:20]}")
    if not uniq:
        raise FileNotFoundError("Could not find bio_resting_5min_100hz.csv anywhere accessible.")
    return uniq[0]


def flatten_feature_frames(frames):
    parts = []
    for obj in frames:
        if obj is None:
            continue
        if isinstance(obj, pd.Series):
            df = obj.to_frame().T
        else:
            df = pd.DataFrame(obj)
        if len(df) == 0:
            continue
        if len(df) > 1:
            df = df.iloc[[0]].copy()
        parts.append(df.reset_index(drop=True))
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, axis=1)
    out = out.loc[:, ~out.columns.duplicated()]
    return out


def sanitize_for_csv(df):
    clean = pd.DataFrame(index=df.index)
    for col in df.columns:
        val = df.iloc[0][col]
        if isinstance(val, (list, tuple, dict, np.ndarray, pd.Series, pd.DataFrame)):
            continue
        clean[col] = df[col]
    for col in clean.columns:
        clean[col] = pd.to_numeric(clean[col], errors="ignore")
    return clean.replace([np.inf, -np.inf], np.nan)


def compute_with_neurokit(ecg, fs):
    import neurokit2 as nk

    print("Using NeuroKit2 pipeline.")
    cleaned = nk.ecg_clean(np.asarray(ecg, dtype=float), sampling_rate=fs, method="neurokit")
    _, peaks_info = nk.ecg_peaks(cleaned, sampling_rate=fs, method="neurokit", correct_artifacts=True)
    rpeaks = np.asarray(peaks_info["ECG_R_Peaks"], dtype=int)

    if len(rpeaks) < 5:
        raise RuntimeError(f"Too few R-peaks detected by NeuroKit2: {len(rpeaks)}")

    rr_ms = np.diff(rpeaks) / fs * 1000.0
    print(f"Detected R-peaks: {len(rpeaks)}")
    print(
        "RR interval summary (ms): "
        f"mean={np.mean(rr_ms):.3f}, sd={np.std(rr_ms, ddof=1):.3f}, "
        f"min={np.min(rr_ms):.3f}, max={np.max(rr_ms):.3f}"
    )

    peaks_dict = {"ECG_R_Peaks": rpeaks}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        time_df = nk.hrv_time(peaks_dict, sampling_rate=fs, show=False)
        freq_df = nk.hrv_frequency(peaks_dict, sampling_rate=fs, show=False, normalize=True)
        nonlin_df = nk.hrv_nonlinear(peaks_dict, sampling_rate=fs, show=False)

    features = flatten_feature_frames([time_df, freq_df, nonlin_df])
    features.insert(0, "Method", "NeuroKit2")
    features.insert(1, "RPeaks_N", int(len(rpeaks)))
    features.insert(2, "Mean_HR_bpm", float(60000.0 / np.mean(rr_ms)))
    return sanitize_for_csv(features), rpeaks


def bandpower(f, pxx, low, high):
    mask = (f >= low) & (f < high)
    if np.sum(mask) < 2:
        return np.nan
    return float(np.trapz(pxx[mask], f[mask]))


def sample_entropy(x, m=2):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n <= m + 2:
        return np.nan
    sd = np.std(x, ddof=0)
    if sd == 0:
        return 0.0
    r = 0.2 * sd

    def count(mm):
        c = 0
        for i in range(n - mm):
            ti = x[i:i + mm]
            for j in range(i + 1, n - mm + 1):
                if np.max(np.abs(ti - x[j:j + mm])) <= r:
                    c += 1
        return c

    b = count(m)
    a = count(m + 1)
    if b == 0:
        return np.nan
    if a == 0:
        return float(-np.log(1.0 / b))
    return float(-np.log(a / b))


def dfa_alpha(rr_ms):
    x = np.asarray(rr_ms, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 16:
        return np.nan
    y = np.cumsum(x - np.mean(x))
    max_scale = min(n // 4, 32)
    if max_scale < 4:
        return np.nan
    scales = np.unique(np.floor(np.logspace(np.log10(4), np.log10(max_scale), 8)).astype(int))
    valid, flucs = [], []
    for s in scales:
        if n // s < 2:
            continue
        seg_flucs = []
        for start in range(0, n - s + 1, s):
            seg = y[start:start + s]
            t = np.arange(s)
            coeff = np.polyfit(t, seg, 1)
            detrended = seg - np.polyval(coeff, t)
            seg_flucs.append(np.sqrt(np.mean(detrended ** 2)))
        if seg_flucs:
            f = np.sqrt(np.mean(np.asarray(seg_flucs) ** 2))
            if f > 0:
                valid.append(s)
                flucs.append(f)
    if len(valid) < 2:
        return np.nan
    return float(np.polyfit(np.log(valid), np.log(flucs), 1)[0])


def compute_fallback(ecg, fs):
    print("Using fallback SciPy/NumPy pipeline.")
    from scipy.signal import butter, filtfilt, find_peaks, welch

    ecg = np.asarray(ecg, dtype=float)
    ecg = ecg[np.isfinite(ecg)]

    nyq = fs / 2
    b, a = butter(3, [0.5 / nyq, min(35 / nyq, 0.99)], btype="bandpass")
    clean = filtfilt(b, a, ecg)

    distance = int(0.30 * fs)
    prom = max(np.std(clean) * 0.6, np.percentile(np.abs(clean - np.median(clean)), 75) * 0.8)
    peaks, _ = find_peaks(clean, distance=distance, prominence=prom)
    peaks_inv, _ = find_peaks(-clean, distance=distance, prominence=prom)
    if len(peaks_inv) > len(peaks) * 1.2:
        peaks = peaks_inv
    if len(peaks) < 5:
        peaks, _ = find_peaks(clean, distance=distance, prominence=max(np.std(clean) * 0.25, 1e-8))
    if len(peaks) < 5:
        peaks, _ = find_peaks(-clean, distance=distance, prominence=max(np.std(clean) * 0.25, 1e-8))
    if len(peaks) < 5:
        raise RuntimeError(f"Too few R-peaks detected: {len(peaks)}")

    rr_all = np.diff(peaks) / fs * 1000.0
    rr = rr_all[(rr_all >= 300) & (rr_all <= 2000)]
    if len(rr) >= 5:
        med = np.median(rr)
        rr = rr[np.abs(rr - med) <= 0.25 * med]
    if len(rr) < 5:
        rr = rr_all

    diff = np.diff(rr)
    mean_nn = float(np.mean(rr))
    sdnn = float(np.std(rr, ddof=1)) if len(rr) > 1 else np.nan
    rmssd = float(np.sqrt(np.mean(diff ** 2))) if len(diff) else np.nan
    sdsd = float(np.std(diff, ddof=1)) if len(diff) > 1 else np.nan
    nn20 = int(np.sum(np.abs(diff) > 20)) if len(diff) else 0
    nn50 = int(np.sum(np.abs(diff) > 50)) if len(diff) else 0

    # Frequency-domain HRV via 4 Hz interpolated NN tachogram.
    if len(rr) >= 8:
        rr_s = rr / 1000.0
        t_beats = np.cumsum(rr_s)
        t_rr = t_beats - rr_s / 2
        fs_i = 4.0
        t_grid = np.arange(t_rr[0], t_rr[-1], 1 / fs_i)
        rr_i = np.interp(t_grid, t_rr, rr) - np.mean(rr)
        f, pxx = welch(rr_i, fs=fs_i, nperseg=min(256, len(rr_i)), detrend="constant")
        ulf = bandpower(f, pxx, 0.0000, 0.0033)
        vlf = bandpower(f, pxx, 0.0033, 0.0400)
        lf = bandpower(f, pxx, 0.0400, 0.1500)
        hf = bandpower(f, pxx, 0.1500, 0.4000)
        tp = bandpower(f, pxx, 0.0000, 0.4000)
        lfhf = lf / hf if np.isfinite(lf) and np.isfinite(hf) and hf > 0 else np.nan
        lfn = 100 * lf / (lf + hf) if np.isfinite(lf + hf) and (lf + hf) > 0 else np.nan
        hfn = 100 * hf / (lf + hf) if np.isfinite(lf + hf) and (lf + hf) > 0 else np.nan
    else:
        ulf = vlf = lf = hf = tp = lfhf = lfn = hfn = np.nan

    if len(rr) >= 3:
        sd_diff = np.std(diff, ddof=1)
        sd1 = float(np.sqrt(0.5) * sd_diff)
        sd2 = float(np.sqrt(max(2 * sdnn ** 2 - 0.5 * sd_diff ** 2, 0)))
        sd1sd2 = sd1 / sd2 if sd2 > 0 else np.nan
        area = float(np.pi * sd1 * sd2)
    else:
        sd1 = sd2 = sd1sd2 = area = np.nan

    features = pd.DataFrame([{
        "Method": "Fallback_SciPy_NumPy",
        "RPeaks_N": int(len(peaks)),
        "NN_Intervals_N": int(len(rr)),
        "Mean_HR_bpm": float(60000 / mean_nn),
        "HRV_MeanNN": mean_nn,
        "HRV_SDNN": sdnn,
        "HRV_RMSSD": rmssd,
        "HRV_SDSD": sdsd,
        "HRV_CVNN": sdnn / mean_nn if mean_nn else np.nan,
        "HRV_CVSD": rmssd / mean_nn if mean_nn else np.nan,
        "HRV_MedianNN": float(np.median(rr)),
        "HRV_MadNN": float(np.median(np.abs(rr - np.median(rr)))),
        "HRV_MCVNN": float(np.median(np.abs(rr - np.median(rr))) / np.median(rr)),
        "HRV_IQRNN": float(np.percentile(rr, 75) - np.percentile(rr, 25)),
        "HRV_NN20": nn20,
        "HRV_pNN20": float(100 * nn20 / len(diff)) if len(diff) else np.nan,
        "HRV_NN50": nn50,
        "HRV_pNN50": float(100 * nn50 / len(diff)) if len(diff) else np.nan,
        "HRV_MinNN": float(np.min(rr)),
        "HRV_MaxNN": float(np.max(rr)),
        "HRV_SDHR": float(np.std(60000 / rr, ddof=1)) if len(rr) > 1 else np.nan,
        "HRV_ULF": ulf,
        "HRV_VLF": vlf,
        "HRV_LF": lf,
        "HRV_HF": hf,
        "HRV_TP": tp,
        "HRV_LFHF": lfhf,
        "HRV_LFn": lfn,
        "HRV_HFn": hfn,
        "HRV_SD1": sd1,
        "HRV_SD2": sd2,
        "HRV_SD1SD2": sd1sd2,
        "HRV_S": area,
        "HRV_SampEn": sample_entropy(rr, 2),
        "HRV_DFA_alpha1": dfa_alpha(rr),
    }])

    print(f"Detected R-peaks: {len(peaks)}")
    print(
        "RR interval summary after filtering (ms): "
        f"n={len(rr)}, mean={np.mean(rr):.3f}, sd={np.std(rr, ddof=1):.3f}, "
        f"min={np.min(rr):.3f}, max={np.max(rr):.3f}"
    )
    return sanitize_for_csv(features), peaks


def main():
    input_path = find_input_file()
    print(f"Loading input file: {input_path}")
    data = pd.read_csv(input_path)
    print(f"Input shape: {data.shape}")
    print(f"Input columns: {list(data.columns)}")

    if "ECG" not in data.columns:
        raise ValueError("Input CSV has no ECG column.")

    ecg = pd.to_numeric(data["ECG"], errors="coerce")
    if ecg.isna().any():
        print(f"ECG non-finite/NaN count before interpolation: {int(ecg.isna().sum())}")
        ecg = ecg.interpolate(limit_direction="both").fillna(0)
    ecg = ecg.to_numpy(dtype=float)

    duration_s = len(ecg) / FS
    print(f"ECG samples={len(ecg)}, sampling_rate={FS} Hz, duration={duration_s:.2f} s")

    try:
        features, rpeaks = compute_with_neurokit(ecg, FS)
    except Exception as exc:
        print("NeuroKit2 pipeline unavailable or failed; switching to fallback.")
        print(f"Reason: {repr(exc)}")
        print(traceback.format_exc(limit=3))
        features, rpeaks = compute_fallback(ecg, FS)

    if "Sampling_Rate_Hz" not in features.columns:
        features.insert(1, "Sampling_Rate_Hz", FS)
    if "Signal_Duration_s" not in features.columns:
        features.insert(2, "Signal_Duration_s", duration_s)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    features.to_csv(OUTPUT_PATH, index=False)

    aux_path = "pred_results/hrv_detected_rpeaks_samples.csv"
    pd.DataFrame({"ECG_R_Peak_Sample": np.asarray(rpeaks, dtype=int)}).to_csv(aux_path, index=False)

    print(f"Saved required HRV feature table to: {OUTPUT_PATH}")
    print(f"Saved auxiliary R-peak indices to: {aux_path}")
    print(f"Output shape: {features.shape}")
    print("Output columns:")
    print(list(features.columns))
    print("Feature preview:")
    with pd.option_context("display.max_columns", min(40, features.shape[1]), "display.width", 220):
        print(features.iloc[:, :min(40, features.shape[1])].to_string(index=False))


if __name__ == "__main__":
    main()