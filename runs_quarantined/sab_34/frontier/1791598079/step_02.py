#!/usr/bin/env python3
"""
Locate the biosignal dataset, then compute HRV indices from bio_resting_5min_100hz.csv
and save them to pred_results/hrv_analysis_pred.csv.

This version is robust to the working directory not being the dataset root.
"""

import os
import glob
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

TARGET_FILENAME = "bio_resting_5min_100hz.csv"
OUTPUT_PATH = "pred_results/hrv_analysis_pred.csv"
FS = 100


def find_input_file():
    candidates = []
    patterns = [
        os.path.join("biosignals", TARGET_FILENAME),
        TARGET_FILENAME,
        os.path.join("*", "biosignals", TARGET_FILENAME),
        os.path.join("..", "biosignals", TARGET_FILENAME),
        os.path.join("..", "*", "biosignals", TARGET_FILENAME),
        os.path.join("..", "..", "biosignals", TARGET_FILENAME),
        os.path.join("..", "..", "*", "biosignals", TARGET_FILENAME),
        os.path.join("/data", "**", "biosignals", TARGET_FILENAME),
        os.path.join("/mnt", "**", "biosignals", TARGET_FILENAME),
    ]
    for pat in patterns:
        candidates.extend(glob.glob(pat, recursive=True))
    candidates = sorted(set(candidates), key=lambda p: (len(os.path.abspath(p)), os.path.abspath(p)))
    print("Current working directory:", os.getcwd())
    print("Dataset search candidates:")
    for c in candidates[:20]:
        print(" -", c)
    if not candidates:
        print("Top-level directory listing:")
        print(os.listdir("."))
        raise FileNotFoundError(f"Could not locate {TARGET_FILENAME}")
    return candidates[0]


def _safe_float(x):
    try:
        x = float(x)
        if np.isfinite(x):
            return x
    except Exception:
        pass
    return np.nan


def detect_peaks_fallback(ecg, fs):
    from scipy.signal import butter, filtfilt, find_peaks

    ecg = np.asarray(ecg, dtype=float)
    ecg = ecg - np.nanmedian(ecg)
    ecg = np.nan_to_num(ecg)

    low = 5.0 / (fs / 2.0)
    high = min(20.0 / (fs / 2.0), 0.95)
    b, a = butter(3, [low, high], btype="bandpass")
    filt = filtfilt(b, a, ecg)

    best = None
    for polarity in (1, -1):
        sig = polarity * filt
        distance = int(0.30 * fs)
        prom = max(0.20 * np.std(sig), np.percentile(sig, 90) - np.percentile(sig, 60))
        peaks, props = find_peaks(sig, distance=distance, prominence=prom)
        hr = len(peaks) / (len(ecg) / fs / 60.0)
        plaus_penalty = 0 if 35 <= hr <= 180 else 1000
        mean_prom = float(np.mean(props["prominences"])) if len(peaks) else 0.0
        score = mean_prom - plaus_penalty
        if best is None or score > best[0]:
            best = (score, peaks, polarity, hr)

    peaks = np.asarray(best[1], dtype=int)
    polarity = best[2]

    # Refine to local extremum in original ECG.
    refined = []
    sig_orig = polarity * ecg
    win = max(1, int(0.08 * fs))
    for p in peaks:
        lo = max(0, p - win)
        hi = min(len(sig_orig), p + win + 1)
        refined.append(lo + int(np.argmax(sig_orig[lo:hi])))
    return np.unique(np.asarray(refined, dtype=int))


def clean_nni_from_peaks(peaks, fs):
    peaks = np.asarray(peaks, dtype=int)
    rr = np.diff(peaks) / fs * 1000.0
    rr = rr[(rr >= 300) & (rr <= 2000)]
    if len(rr) >= 8:
        med = np.median(rr)
        mad = np.median(np.abs(rr - med))
        if mad > 0:
            rr = rr[np.abs(0.6745 * (rr - med) / mad) < 5.0]
    return rr


def sample_entropy(x, m=2, r=None):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < m + 3:
        return np.nan
    if r is None:
        sd = np.std(x)
        if sd <= 0:
            return np.nan
        r = 0.2 * sd

    def count(mm):
        c = 0
        nm = n - mm + 1
        for i in range(nm - 1):
            xi = x[i:i + mm]
            for j in range(i + 1, nm):
                if np.max(np.abs(xi - x[j:j + mm])) <= r:
                    c += 1
        return c

    b = count(m)
    a = count(m + 1)
    return -np.log(a / b) if a > 0 and b > 0 else np.nan


def dfa_alpha(x, scales):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    vals, used = [], []
    if n < 16:
        return np.nan
    y = np.cumsum(x - np.mean(x))
    for s in scales:
        s = int(s)
        if s < 4 or n < 2 * s:
            continue
        nseg = n // s
        fsq = []
        t = np.arange(s)
        for k in range(nseg):
            seg = y[k * s:(k + 1) * s]
            coef = np.polyfit(t, seg, 1)
            detr = seg - np.polyval(coef, t)
            fsq.append(np.mean(detr * detr))
        f = np.sqrt(np.mean(fsq))
        if f > 0:
            vals.append(f)
            used.append(s)
    if len(vals) < 2:
        return np.nan
    return float(np.polyfit(np.log(used), np.log(vals), 1)[0])


def fallback_hrv_features(peaks, fs):
    from scipy.interpolate import interp1d
    from scipy.signal import welch

    features = {}
    peaks = np.asarray(peaks, dtype=int)
    nni = clean_nni_from_peaks(peaks, fs)
    features["HRV_Peak_Count"] = len(peaks)
    features["HRV_NN_Count"] = len(nni)

    if len(nni) < 3:
        return features

    diff = np.diff(nni)
    absdiff = np.abs(diff)

    features["HRV_MeanNN"] = np.mean(nni)
    features["HRV_SDNN"] = np.std(nni, ddof=1)
    features["HRV_RMSSD"] = np.sqrt(np.mean(diff ** 2))
    features["HRV_SDSD"] = np.std(diff, ddof=1) if len(diff) > 1 else np.nan
    features["HRV_CVNN"] = features["HRV_SDNN"] / features["HRV_MeanNN"]
    features["HRV_CVRMSSD"] = features["HRV_RMSSD"] / features["HRV_MeanNN"]
    features["HRV_MedianNN"] = np.median(nni)
    features["HRV_MadNN"] = np.median(np.abs(nni - np.median(nni)))
    features["HRV_MCVNN"] = features["HRV_MadNN"] / features["HRV_MedianNN"]
    features["HRV_IQRNN"] = np.percentile(nni, 75) - np.percentile(nni, 25)
    features["HRV_pNN50"] = 100.0 * np.mean(absdiff > 50) if len(diff) else np.nan
    features["HRV_pNN20"] = 100.0 * np.mean(absdiff > 20) if len(diff) else np.nan
    features["HRV_MinNN"] = np.min(nni)
    features["HRV_MaxNN"] = np.max(nni)
    hist = np.histogram(nni, bins="auto")[0]
    features["HRV_HTI"] = len(nni) / np.max(hist) if len(hist) and np.max(hist) > 0 else np.nan

    # Frequency domain from interpolated NN interval time series.
    for name in ["ULF", "VLF", "LF", "HF", "VHF", "TP", "LFHF", "LFn", "HFn", "LnHF"]:
        features["HRV_" + name] = np.nan

    try:
        rr_all = np.diff(peaks) / fs * 1000.0
        t_all = peaks[1:] / fs
        mask = (rr_all >= 300) & (rr_all <= 2000)
        t, rr = t_all[mask], rr_all[mask]
        if len(rr) >= 8:
            med = np.median(rr)
            mad = np.median(np.abs(rr - med))
            if mad > 0:
                keep = np.abs(0.6745 * (rr - med) / mad) < 5.0
                t, rr = t[keep], rr[keep]
        if len(rr) >= 8 and (t[-1] - t[0]) > 30:
            fs_i = 4.0
            tg = np.arange(t[0], t[-1], 1 / fs_i)
            yg = interp1d(t, rr, kind="linear", fill_value="extrapolate")(tg)
            yg = yg - np.mean(yg)
            freqs, psd = welch(yg, fs=fs_i, nperseg=min(256, len(yg)))

            def bp(lo, hi):
                m = (freqs >= lo) & (freqs < hi)
                return float(np.trapz(psd[m], freqs[m])) if np.sum(m) >= 2 else np.nan

            vlf = bp(0.0033, 0.04)
            lf = bp(0.04, 0.15)
            hf = bp(0.15, 0.40)
            tp = bp(0.0033, 0.40)
            features["HRV_VLF"] = vlf
            features["HRV_LF"] = lf
            features["HRV_HF"] = hf
            features["HRV_TP"] = tp
            features["HRV_LFHF"] = lf / hf if np.isfinite(lf) and np.isfinite(hf) and hf > 0 else np.nan
            denom = lf + hf if np.isfinite(lf) and np.isfinite(hf) else np.nan
            features["HRV_LFn"] = lf / denom if np.isfinite(denom) and denom > 0 else np.nan
            features["HRV_HFn"] = hf / denom if np.isfinite(denom) and denom > 0 else np.nan
            features["HRV_LnHF"] = np.log(hf) if np.isfinite(hf) and hf > 0 else np.nan
    except Exception as e:
        print("Fallback frequency-domain calculation failed:", repr(e))

    sdnn = features["HRV_SDNN"]
    rmssd = features["HRV_RMSSD"]
    features["HRV_SD1"] = rmssd / np.sqrt(2)
    v = 2 * sdnn ** 2 - 0.5 * rmssd ** 2
    features["HRV_SD2"] = np.sqrt(v) if v > 0 else np.nan
    features["HRV_SD1SD2"] = features["HRV_SD1"] / features["HRV_SD2"] if np.isfinite(features["HRV_SD2"]) and features["HRV_SD2"] > 0 else np.nan
    features["HRV_S"] = np.pi * features["HRV_SD1"] * features["HRV_SD2"] if np.isfinite(features["HRV_SD2"]) else np.nan
    features["HRV_SampEn"] = sample_entropy(nni)
    features["HRV_DFA_alpha1"] = dfa_alpha(nni, np.arange(4, 17))
    features["HRV_DFA_alpha2"] = dfa_alpha(nni, np.arange(16, 65))
    return features


def compute_with_neurokit(ecg, fs):
    import neurokit2 as nk

    cleaned = nk.ecg_clean(ecg, sampling_rate=fs, method="neurokit")
    _, info = nk.ecg_peaks(cleaned, sampling_rate=fs, method="neurokit", correct_artifacts=True)
    peaks = np.asarray(info["ECG_R_Peaks"], dtype=int)
    if len(peaks) < 5:
        raise RuntimeError("Too few NeuroKit peaks")

    pk = {"ECG_R_Peaks": peaks}
    frames = [
        nk.hrv_time(pk, sampling_rate=fs, show=False),
        nk.hrv_frequency(pk, sampling_rate=fs, show=False),
        nk.hrv_nonlinear(pk, sampling_rate=fs, show=False),
    ]
    df = pd.concat([f.reset_index(drop=True) for f in frames], axis=1)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df.insert(0, "HRV_NN_Count", max(len(peaks) - 1, 0))
    df.insert(0, "HRV_Peak_Count", len(peaks))
    return df, peaks


def main():
    input_path = find_input_file()
    print("Using input file:", input_path)
    data = pd.read_csv(input_path)
    print("Loaded shape:", data.shape)
    print("Columns:", list(data.columns))

    if "ECG" not in data.columns:
        raise ValueError("No ECG column found.")

    ecg = pd.to_numeric(data["ECG"], errors="coerce").interpolate().bfill().ffill().to_numpy(float)
    duration_s = len(ecg) / FS
    print(f"Samples={len(ecg)}, fs={FS} Hz, duration={duration_s:.2f} s")

    try:
        features_df, peaks = compute_with_neurokit(ecg, FS)
        method = "NeuroKit2"
    except Exception as e:
        print("NeuroKit2 unavailable or failed:", repr(e))
        peaks = detect_peaks_fallback(ecg, FS)
        features_df = pd.DataFrame([fallback_hrv_features(peaks, FS)])
        method = "scipy_fallback"

    hr_bpm = len(peaks) / (duration_s / 60.0)
    print(f"Detection method: {method}")
    print(f"Detected R-peaks: {len(peaks)}")
    print(f"Mean HR by peak count: {hr_bpm:.2f} bpm")

    for col in features_df.columns:
        if features_df[col].dtype == object:
            continue
        features_df[col] = features_df[col].map(_safe_float)

    features_df["ECG_Sampling_Rate_Hz"] = FS
    features_df["ECG_Duration_s"] = duration_s
    features_df["ECG_Peak_Detection_Method"] = method

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    features_df.to_csv(OUTPUT_PATH, index=False)

    print("Output feature table shape:", features_df.shape)
    key_cols = [c for c in ["HRV_Peak_Count", "HRV_NN_Count", "HRV_MeanNN", "HRV_SDNN", "HRV_RMSSD",
                            "HRV_LF", "HRV_HF", "HRV_LFHF", "HRV_SD1", "HRV_SD2", "HRV_SampEn"] if c in features_df.columns]
    print("Selected features:")
    print(features_df[key_cols].to_string(index=False))
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()