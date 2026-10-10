#!/usr/bin/env python3
"""
Compute HRV indices from biosignals/bio_resting_5min_100hz.csv and save:
pred_results/hrv_analysis_pred.csv

The script prefers NeuroKit2 for ECG cleaning, R-peak detection, and HRV feature
extraction. If NeuroKit2 is unavailable or fails, it falls back to a SciPy/NumPy
implementation with standard time-, frequency-, and non-linear HRV metrics.
"""

import os
import warnings
import traceback
import numpy as np
import pandas as pd

INPUT_PATH = "biosignals/bio_resting_5min_100hz.csv"
OUTPUT_PATH = "pred_results/hrv_analysis_pred.csv"
FS = 100  # Hz, from filename/task description


def _flatten_feature_frames(frames):
    """Concatenate one-row feature frames/series into a single one-row DataFrame."""
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


def _sanitize_for_csv(df):
    """Keep scalar-compatible columns and coerce numeric-looking values."""
    clean = pd.DataFrame(index=df.index)
    for col in df.columns:
        val = df.iloc[0][col]
        if isinstance(val, (list, tuple, dict, np.ndarray, pd.Series, pd.DataFrame)):
            continue
        clean[col] = df[col]
    for col in clean.columns:
        clean[col] = pd.to_numeric(clean[col], errors="ignore")
    return clean


def compute_with_neurokit(ecg, fs):
    import neurokit2 as nk

    print("Using NeuroKit2 pipeline.")
    ecg = np.asarray(ecg, dtype=float)

    # Clean ECG then detect R peaks.
    cleaned = nk.ecg_clean(ecg, sampling_rate=fs, method="neurokit")
    _, peaks_info = nk.ecg_peaks(cleaned, sampling_rate=fs, method="neurokit", correct_artifacts=True)
    rpeaks = np.asarray(peaks_info["ECG_R_Peaks"], dtype=int)

    if len(rpeaks) < 5:
        raise RuntimeError(f"Too few ECG peaks detected by NeuroKit2: {len(rpeaks)}")

    print(f"Detected R-peaks: {len(rpeaks)}")
    rr_ms = np.diff(rpeaks) / fs * 1000.0
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

    features = _flatten_feature_frames([time_df, freq_df, nonlin_df])
    features.insert(0, "RPeaks_N", len(rpeaks))
    features.insert(1, "Mean_HR_bpm", 60000.0 / np.mean(rr_ms))

    # Add method metadata as columns useful for reproducibility.
    features.insert(0, "Method", "NeuroKit2")
    return _sanitize_for_csv(features), rpeaks


def _welch_psd(x, fs, nperseg=None):
    from scipy.signal import welch

    if nperseg is None:
        nperseg = min(256, len(x))
    f, pxx = welch(x, fs=fs, nperseg=nperseg, detrend="constant")
    return f, pxx


def _bandpower(f, pxx, low, high):
    mask = (f >= low) & (f < high)
    if np.sum(mask) < 2:
        return np.nan
    return float(np.trapz(pxx[mask], f[mask]))


def _sample_entropy(x, m=2, r=None):
    """Simple sample entropy implementation for a short RR series."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n <= m + 2:
        return np.nan
    if r is None:
        sd = np.std(x, ddof=0)
        if sd == 0:
            return 0.0
        r = 0.2 * sd

    def count_matches(mm):
        count = 0
        total = 0
        for i in range(n - mm):
            template = x[i:i + mm]
            for j in range(i + 1, n - mm + 1):
                total += 1
                if np.max(np.abs(template - x[j:j + mm])) <= r:
                    count += 1
        return count, total

    b, _ = count_matches(m)
    a, _ = count_matches(m + 1)
    if b == 0:
        return np.inf
    if a == 0:
        return -np.log(1.0 / b)
    return float(-np.log(a / b))


def _dfa_alpha(rr_ms):
    """Approximate DFA alpha over available small scales."""
    x = np.asarray(rr_ms, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 16:
        return np.nan
    y = np.cumsum(x - np.mean(x))
    max_scale = max(4, min(n // 4, 32))
    scales = np.unique(np.floor(np.logspace(np.log10(4), np.log10(max_scale), 8)).astype(int))
    flucts = []
    valid_scales = []
    for s in scales:
        if s < 4 or n // s < 2:
            continue
        rms_segments = []
        for start in range(0, n - s + 1, s):
            seg = y[start:start + s]
            t = np.arange(s)
            coeff = np.polyfit(t, seg, 1)
            trend = np.polyval(coeff, t)
            rms_segments.append(np.sqrt(np.mean((seg - trend) ** 2)))
        if rms_segments:
            fluct = np.sqrt(np.mean(np.square(rms_segments)))
            if fluct > 0:
                flucts.append(fluct)
                valid_scales.append(s)
    if len(valid_scales) < 2:
        return np.nan
    return float(np.polyfit(np.log(valid_scales), np.log(flucts), 1)[0])


def compute_fallback(ecg, fs):
    print("Using fallback SciPy/NumPy pipeline.")
    from scipy.signal import butter, filtfilt, find_peaks

    ecg = np.asarray(ecg, dtype=float)
    ecg = ecg[np.isfinite(ecg)]

    # Bandpass for QRS enhancement.
    nyq = fs / 2.0
    low = 0.5 / nyq
    high = min(35.0 / nyq, 0.99)
    b, a = butter(3, [low, high], btype="bandpass")
    clean = filtfilt(b, a, ecg)

    # Robust peak detection: minimum distance 0.3 s, adaptive prominence.
    distance = int(0.30 * fs)
    prominence = max(np.std(clean) * 0.6, np.percentile(np.abs(clean - np.median(clean)), 75) * 0.8)
    peaks, props = find_peaks(clean, distance=distance, prominence=prominence)

    # If inverted ECG yields more plausible peaks, use inverted signal.
    peaks_inv, props_inv = find_peaks(-clean, distance=distance, prominence=prominence)
    if len(peaks_inv) > len(peaks) * 1.2:
        peaks = peaks_inv
        clean = -clean

    if len(peaks) < 5:
        # Relax threshold once.
        peaks, props = find_peaks(clean, distance=distance, prominence=max(np.std(clean) * 0.25, 1e-8))

    if len(peaks) < 5:
        raise RuntimeError(f"Too few ECG peaks detected by fallback method: {len(peaks)}")

    rr_ms_all = np.diff(peaks) / fs * 1000.0

    # Artifact filter: keep physiologically plausible intervals and remove extreme local deviations.
    plausible = (rr_ms_all >= 300) & (rr_ms_all <= 2000)
    rr_ms = rr_ms_all[plausible]
    if len(rr_ms) >= 5:
        med = np.median(rr_ms)
        rr_ms = rr_ms[np.abs(rr_ms - med) <= 0.25 * med]
    else:
        rr_ms = rr_ms_all

    rr_s = rr_ms / 1000.0
    diff_rr = np.diff(rr_ms)

    # Time-domain indices.
    mean_nn = float(np.mean(rr_ms))
    sdnn = float(np.std(rr_ms, ddof=1)) if len(rr_ms) > 1 else np.nan
    rmssd = float(np.sqrt(np.mean(diff_rr ** 2))) if len(diff_rr) else np.nan
    sdsd = float(np.std(diff_rr, ddof=1)) if len(diff_rr) > 1 else np.nan
    nn20 = int(np.sum(np.abs(diff_rr) > 20)) if len(diff_rr) else 0
    nn50 = int(np.sum(np.abs(diff_rr) > 50)) if len(diff_rr) else 0
    pnn20 = float(100.0 * nn20 / len(diff_rr)) if len(diff_rr) else np.nan
    pnn50 = float(100.0 * nn50 / len(diff_rr)) if len(diff_rr) else np.nan
    mean_hr = float(60000.0 / mean_nn)
    sd_hr = float(np.std(60000.0 / rr_ms, ddof=1)) if len(rr_ms) > 1 else np.nan

    # Frequency-domain: interpolate tachogram at 4 Hz.
    if len(rr_ms) >= 8:
        t_beats = np.cumsum(rr_s)
        t_rr = t_beats - rr_s / 2.0
        fs_interp = 4.0
        t_grid = np.arange(t_rr[0], t_rr[-1], 1.0 / fs_interp)
        rr_interp = np.interp(t_grid, t_rr, rr_ms)
        rr_interp = rr_interp - np.mean(rr_interp)
        f, pxx = _welch_psd(rr_interp, fs=fs_interp, nperseg=min(256, len(rr_interp)))
        ulf = _bandpower(f, pxx, 0.000, 0.0033)
        vlf = _bandpower(f, pxx, 0.0033, 0.04)
        lf = _bandpower(f, pxx, 0.04, 0.15)
        hf = _bandpower(f, pxx, 0.15, 0.40)
        total = _bandpower(f, pxx, 0.000, 0.40)
        lfhf = lf / hf if np.isfinite(lf) and np.isfinite(hf) and hf > 0 else np.nan
        lfn = 100 * lf / (lf + hf) if (lf + hf) > 0 else np.nan
        hfn = 100 * hf / (lf + hf) if (lf + hf) > 0 else np.nan
    else:
        ulf = vlf = lf = hf = total = lfhf = lfn = hfn = np.nan

    # Non-linear Poincare and entropy/fractal metrics.
    if len(rr_ms) >= 3:
        sd1 = float(np.sqrt(0.5) * np.std(diff_rr, ddof=1))
        sd2_arg = 2 * sdnn ** 2 - 0.5 * np.std(diff_rr, ddof=1) ** 2
        sd2 = float(np.sqrt(max(sd2_arg, 0)))
        sd1sd2 = sd1 / sd2 if sd2 > 0 else np.nan
        poincare_area = float(np.pi * sd1 * sd2)
    else:
        sd1 = sd2 = sd1sd2 = poincare_area = np.nan

    sampen = _sample_entropy(rr_ms, m=2)
    dfa = _dfa_alpha(rr_ms)

    features = pd.DataFrame([{
        "Method": "Fallback_SciPy_NumPy",
        "RPeaks_N": int(len(peaks)),
        "NN_Intervals_N": int(len(rr_ms)),
        "Mean_HR_bpm": mean_hr,
        "HRV_MeanNN": mean_nn,
        "HRV_SDNN": sdnn,
        "HRV_RMSSD": rmssd,
        "HRV_SDSD": sdsd,
        "HRV_CVNN": sdnn / mean_nn if mean_nn else np.nan,
        "HRV_CVSD": rmssd / mean_nn if mean_nn else np.nan,
        "HRV_MedianNN": float(np.median(rr_ms)),
        "HRV_MadNN": float(np.median(np.abs(rr_ms - np.median(rr_ms)))),
        "HRV_MCVNN": float(np.median(np.abs(rr_ms - np.median(rr_ms))) / np.median(rr_ms)),
        "HRV_IQRNN": float(np.percentile(rr_ms, 75) - np.percentile(rr_ms, 25)),
        "HRV_NN20": nn20,
        "HRV_pNN20": pnn20,
        "HRV_NN50": nn50,
        "HRV_pNN50": pnn50,
        "HRV_MinNN": float(np.min(rr_ms)),
        "HRV_MaxNN": float(np.max(rr_ms)),
        "HRV_SDHR": sd_hr,
        "HRV_ULF": ulf,
        "HRV_VLF": vlf,
        "HRV_LF": lf,
        "HRV_HF": hf,
        "HRV_TP": total,
        "HRV_LFHF": lfhf,
        "HRV_LFn": lfn,
        "HRV_HFn": hfn,
        "HRV_SD1": sd1,
        "HRV_SD2": sd2,
        "HRV_SD1SD2": sd1sd2,
        "HRV_S": poincare_area,
        "HRV_SampEn": sampen,
        "HRV_DFA_alpha1": dfa,
    }])

    print(f"Detected R-peaks: {len(peaks)}")
    print(
        "RR interval summary after filtering (ms): "
        f"n={len(rr_ms)}, mean={np.mean(rr_ms):.3f}, sd={np.std(rr_ms, ddof=1):.3f}, "
        f"min={np.min(rr_ms):.3f}, max={np.max(rr_ms):.3f}"
    )

    return _sanitize_for_csv(features), peaks


def main():
    print(f"Loading input file: {INPUT_PATH}")
    data = pd.read_csv(INPUT_PATH)
    print(f"Input shape: {data.shape}")
    print(f"Input columns: {list(data.columns)}")

    if "ECG" not in data.columns:
        raise ValueError("Expected an ECG column in the input file.")

    ecg = pd.to_numeric(data["ECG"], errors="coerce").to_numpy(dtype=float)
    n_missing = int(np.sum(~np.isfinite(ecg)))
    if n_missing:
        print(f"Warning: ECG contains {n_missing} non-finite samples; interpolating/filling.")
        s = pd.Series(ecg).interpolate(limit_direction="both").fillna(0)
        ecg = s.to_numpy(dtype=float)

    duration_s = len(ecg) / FS
    print(f"ECG samples: {len(ecg)}, sampling rate: {FS} Hz, duration: {duration_s:.2f} s")

    try:
        features, rpeaks = compute_with_neurokit(ecg, FS)
    except Exception as exc:
        print("NeuroKit2 pipeline unavailable or failed; switching to fallback.")
        print(f"Reason: {repr(exc)}")
        print(traceback.format_exc(limit=2))
        features, rpeaks = compute_fallback(ecg, FS)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Add core provenance/detection fields if absent.
    if "Sampling_Rate_Hz" not in features.columns:
        features.insert(1, "Sampling_Rate_Hz", FS)
    if "Signal_Duration_s" not in features.columns:
        features.insert(2, "Signal_Duration_s", duration_s)

    # Replace infinities with NaN for a clean CSV.
    features = features.replace([np.inf, -np.inf], np.nan)

    features.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved HRV feature table to: {OUTPUT_PATH}")
    print(f"Output shape: {features.shape}")
    print("First 30 output columns:")
    print(list(features.columns[:30]))
    print("Feature preview:")
    with pd.option_context("display.max_columns", 20, "display.width", 180):
        print(features.iloc[:, :min(20, features.shape[1])].to_string(index=False))

    # Save detected peaks as an auxiliary reproducibility artifact (not required, but useful).
    aux_path = "pred_results/hrv_detected_rpeaks_samples.csv"
    pd.DataFrame({"ECG_R_Peak_Sample": np.asarray(rpeaks, dtype=int)}).to_csv(aux_path, index=False)
    print(f"Saved auxiliary detected R-peak sample indices to: {aux_path}")


if __name__ == "__main__":
    main()