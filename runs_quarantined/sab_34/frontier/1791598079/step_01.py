#!/usr/bin/env python3
"""
Compute HRV indices from biosignals/bio_resting_5min_100hz.csv.

The script:
1. Reads the 5-minute resting ECG sampled at 100 Hz.
2. Detects ECG R-peaks.
3. Computes HRV features from:
   - time domain
   - frequency domain
   - non-linear domain
4. Saves a one-row feature table to pred_results/hrv_analysis_pred.csv.

It prefers NeuroKit2 if available, with a scipy/numpy fallback implementation.
"""

import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

INPUT_PATH = "biosignals/bio_resting_5min_100hz.csv"
OUTPUT_PATH = "pred_results/hrv_analysis_pred.csv"
FS = 100


def _safe_float(x):
    try:
        x = float(x)
        if np.isfinite(x):
            return x
    except Exception:
        pass
    return np.nan


def detect_peaks_fallback(ecg, fs):
    """Fallback ECG R-peak detection using scipy filtering and peak finding."""
    from scipy.signal import butter, filtfilt, find_peaks

    ecg = np.asarray(ecg, dtype=float)
    ecg = ecg - np.nanmedian(ecg)
    ecg = np.nan_to_num(ecg)

    # Bandpass emphasizes QRS energy. Upper cutoff kept below Nyquist.
    low = 5.0 / (fs / 2.0)
    high = min(20.0 / (fs / 2.0), 0.95)
    b, a = butter(3, [low, high], btype="bandpass")
    filt = filtfilt(b, a, ecg)

    # Try both polarities; choose plausible and higher-prominence solution.
    candidates = []
    for polarity in [1, -1]:
        sig = polarity * filt
        prom = max(0.25 * np.nanstd(sig), np.percentile(sig, 85) - np.percentile(sig, 50))
        distance = int(0.30 * fs)  # max 200 bpm
        peaks, props = find_peaks(sig, distance=distance, prominence=prom)

        if len(peaks) > 2:
            duration_min = len(ecg) / fs / 60.0
            hr = len(peaks) / duration_min
            mean_prom = float(np.nanmean(props.get("prominences", [0])))
            plausible = 35 <= hr <= 180
            score = mean_prom - (0 if plausible else 10)
        else:
            hr = np.nan
            score = -np.inf

        candidates.append((score, peaks, polarity, hr))

    candidates.sort(key=lambda z: z[0], reverse=True)
    peaks = candidates[0][1]

    # Refine each peak to local extremum in the original ECG around detected location.
    refined = []
    window = int(0.08 * fs)
    polarity = candidates[0][2]
    sig_orig = polarity * ecg
    for p in peaks:
        lo = max(0, p - window)
        hi = min(len(ecg), p + window + 1)
        if hi > lo:
            refined.append(lo + int(np.argmax(sig_orig[lo:hi])))
    peaks = np.unique(np.asarray(refined, dtype=int))

    return peaks


def clean_nni_from_peaks(peaks, fs):
    """Return NN intervals in ms after simple physiological/artifact filtering."""
    peaks = np.asarray(peaks, dtype=int)
    rr_ms = np.diff(peaks) / fs * 1000.0

    # Physiological resting/wake limits, broad enough not to over-clean.
    mask = (rr_ms >= 300) & (rr_ms <= 2000)
    rr_ms = rr_ms[mask]

    if len(rr_ms) >= 5:
        med = np.nanmedian(rr_ms)
        mad = np.nanmedian(np.abs(rr_ms - med))
        if mad > 0:
            robust_z = 0.6745 * (rr_ms - med) / mad
            rr_ms = rr_ms[np.abs(robust_z) < 5.0]

    return rr_ms


def sampen(x, m=2, r=None):
    """Simple sample entropy implementation."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < m + 2:
        return np.nan
    if r is None:
        sd = np.std(x, ddof=0)
        if sd <= 0:
            return np.nan
        r = 0.2 * sd

    def count_matches(mm):
        count = 0
        total_templates = n - mm + 1
        for i in range(total_templates - 1):
            template = x[i : i + mm]
            comp = x[i + 1 : total_templates + i * 0]  # placeholder unused
            for j in range(i + 1, total_templates):
                if np.max(np.abs(template - x[j : j + mm])) <= r:
                    count += 1
        return count

    b = count_matches(m)
    a = count_matches(m + 1)
    if b == 0 or a == 0:
        return np.nan
    return -np.log(a / b)


def dfa_alpha(x, scales):
    """Compute DFA scaling exponent over given integer scales."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < max(scales) * 2:
        return np.nan

    y = np.cumsum(x - np.mean(x))
    flucts = []
    used_scales = []

    for s in scales:
        s = int(s)
        if s < 4 or n < 2 * s:
            continue
        nseg = n // s
        rms = []
        for v in range(nseg):
            seg = y[v * s : (v + 1) * s]
            t = np.arange(s)
            coef = np.polyfit(t, seg, 1)
            trend = np.polyval(coef, t)
            rms.append(np.sqrt(np.mean((seg - trend) ** 2)))
        if len(rms) > 0:
            f = np.sqrt(np.mean(np.asarray(rms) ** 2))
            if f > 0:
                flucts.append(f)
                used_scales.append(s)

    if len(flucts) < 2:
        return np.nan
    return float(np.polyfit(np.log(used_scales), np.log(flucts), 1)[0])


def fallback_hrv_features(peaks, fs):
    """Fallback time, frequency, and nonlinear HRV features."""
    from scipy.interpolate import interp1d
    from scipy.signal import welch

    features = {}
    nni = clean_nni_from_peaks(peaks, fs)
    peaks = np.asarray(peaks, dtype=int)

    features["HRV_Peak_Count"] = len(peaks)
    features["HRV_NN_Count"] = len(nni)

    if len(nni) < 3:
        return features

    diff = np.diff(nni)

    # Time-domain features.
    features["HRV_MeanNN"] = np.mean(nni)
    features["HRV_SDNN"] = np.std(nni, ddof=1) if len(nni) > 1 else np.nan
    features["HRV_RMSSD"] = np.sqrt(np.mean(diff**2)) if len(diff) else np.nan
    features["HRV_SDSD"] = np.std(diff, ddof=1) if len(diff) > 1 else np.nan
    features["HRV_CVNN"] = features["HRV_SDNN"] / features["HRV_MeanNN"]
    features["HRV_CVRMSSD"] = features["HRV_RMSSD"] / features["HRV_MeanNN"]
    features["HRV_MedianNN"] = np.median(nni)
    features["HRV_MadNN"] = np.median(np.abs(nni - np.median(nni)))
    features["HRV_MCVNN"] = features["HRV_MadNN"] / features["HRV_MedianNN"]
    features["HRV_IQRNN"] = np.percentile(nni, 75) - np.percentile(nni, 25)
    features["HRV_pNN50"] = 100.0 * np.mean(np.abs(diff) > 50) if len(diff) else np.nan
    features["HRV_pNN20"] = 100.0 * np.mean(np.abs(diff) > 20) if len(diff) else np.nan
    features["HRV_MinNN"] = np.min(nni)
    features["HRV_MaxNN"] = np.max(nni)
    features["HRV_HTI"] = len(nni) / np.max(np.histogram(nni, bins="auto")[0])

    # Frequency-domain features by interpolating tachogram to 4 Hz.
    try:
        beat_times = peaks[1:] / fs
        valid_rr = np.diff(peaks) / fs * 1000.0
        valid_mask = (valid_rr >= 300) & (valid_rr <= 2000)
        t = beat_times[valid_mask]
        y = valid_rr[valid_mask]

        if len(y) >= 8:
            # Mild robust cleanup for interpolation.
            med = np.median(y)
            mad = np.median(np.abs(y - med))
            if mad > 0:
                keep = np.abs(0.6745 * (y - med) / mad) < 5
                t, y = t[keep], y[keep]

        if len(y) >= 8 and t[-1] - t[0] > 60:
            fs_interp = 4.0
            t_grid = np.arange(t[0], t[-1], 1.0 / fs_interp)
            interp = interp1d(t, y, kind="linear", bounds_error=False, fill_value="extrapolate")
            y_grid = interp(t_grid)
            y_grid = y_grid - np.mean(y_grid)
            nperseg = min(256, len(y_grid))
            freqs, psd = welch(y_grid, fs=fs_interp, nperseg=nperseg)

            def bandpower(lo, hi):
                mask = (freqs >= lo) & (freqs < hi)
                if not np.any(mask):
                    return np.nan
                return float(np.trapz(psd[mask], freqs[mask]))

            vlf = bandpower(0.0033, 0.04)
            lf = bandpower(0.04, 0.15)
            hf = bandpower(0.15, 0.40)
            total = bandpower(0.0033, 0.40)

            features["HRV_ULF"] = np.nan
            features["HRV_VLF"] = vlf
            features["HRV_LF"] = lf
            features["HRV_HF"] = hf
            features["HRV_VHF"] = np.nan
            features["HRV_TP"] = total
            features["HRV_LFHF"] = lf / hf if hf and hf > 0 else np.nan
            denom = lf + hf
            features["HRV_LFn"] = lf / denom if denom and denom > 0 else np.nan
            features["HRV_HFn"] = hf / denom if denom and denom > 0 else np.nan
            features["HRV_LnHF"] = np.log(hf) if hf and hf > 0 else np.nan
        else:
            for k in ["ULF", "VLF", "LF", "HF", "VHF", "TP", "LFHF", "LFn", "HFn", "LnHF"]:
                features[f"HRV_{k}"] = np.nan
    except Exception:
        for k in ["ULF", "VLF", "LF", "HF", "VHF", "TP", "LFHF", "LFn", "HFn", "LnHF"]:
            features[f"HRV_{k}"] = np.nan

    # Non-linear features.
    sdnn = features.get("HRV_SDNN", np.nan)
    rmssd = features.get("HRV_RMSSD", np.nan)
    features["HRV_SD1"] = rmssd / np.sqrt(2.0) if np.isfinite(rmssd) else np.nan
    val = 2 * sdnn**2 - 0.5 * rmssd**2 if np.isfinite(sdnn) and np.isfinite(rmssd) else np.nan
    features["HRV_SD2"] = np.sqrt(val) if np.isfinite(val) and val > 0 else np.nan
    features["HRV_SD1SD2"] = (
        features["HRV_SD1"] / features["HRV_SD2"]
        if np.isfinite(features["HRV_SD1"]) and np.isfinite(features["HRV_SD2"]) and features["HRV_SD2"] > 0
        else np.nan
    )
    features["HRV_SampEn"] = sampen(nni, m=2)
    features["HRV_DFA_alpha1"] = dfa_alpha(nni, scales=np.arange(4, 17))
    features["HRV_DFA_alpha2"] = dfa_alpha(nni, scales=np.arange(16, 65))

    return features


def compute_with_neurokit(ecg, fs):
    """Compute HRV using NeuroKit2 if installed and functional."""
    import neurokit2 as nk

    cleaned = nk.ecg_clean(ecg, sampling_rate=fs, method="neurokit")
    _, info = nk.ecg_peaks(cleaned, sampling_rate=fs, method="neurokit", correct_artifacts=True)
    peaks = np.asarray(info["ECG_R_Peaks"], dtype=int)

    if len(peaks) < 5:
        raise RuntimeError("NeuroKit2 detected too few peaks.")

    peaks_dict = {"ECG_R_Peaks": peaks}

    hrv_time = nk.hrv_time(peaks_dict, sampling_rate=fs, show=False)
    hrv_freq = nk.hrv_frequency(peaks_dict, sampling_rate=fs, show=False)
    hrv_nonlin = nk.hrv_nonlinear(peaks_dict, sampling_rate=fs, show=False)

    features_df = pd.concat(
        [
            hrv_time.reset_index(drop=True),
            hrv_freq.reset_index(drop=True),
            hrv_nonlin.reset_index(drop=True),
        ],
        axis=1,
    )

    # Remove duplicate columns, if any.
    features_df = features_df.loc[:, ~features_df.columns.duplicated()].copy()
    features_df.insert(0, "HRV_NN_Count", max(len(peaks) - 1, 0))
    features_df.insert(0, "HRV_Peak_Count", len(peaks))
    return features_df, peaks


def main():
    print(f"Reading input: {INPUT_PATH}")
    data = pd.read_csv(INPUT_PATH)
    print(f"Loaded shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")

    if "ECG" not in data.columns:
        raise ValueError("Input file does not contain an ECG column.")

    ecg = pd.to_numeric(data["ECG"], errors="coerce").interpolate().bfill().ffill().to_numpy(dtype=float)
    duration_s = len(ecg) / FS
    print(f"ECG samples: {len(ecg)}")
    print(f"Sampling rate: {FS} Hz")
    print(f"Duration: {duration_s:.2f} s ({duration_s / 60:.2f} min)")

    method = None
    features_df = None
    peaks = None

    try:
        features_df, peaks = compute_with_neurokit(ecg, FS)
        method = "NeuroKit2"
    except Exception as e:
        print(f"NeuroKit2 path unavailable/failed: {repr(e)}")
        print("Using scipy/numpy fallback implementation.")
        peaks = detect_peaks_fallback(ecg, FS)
        features = fallback_hrv_features(peaks, FS)
        features_df = pd.DataFrame([features])
        method = "fallback"

    peaks = np.asarray(peaks, dtype=int)
    hr_bpm = len(peaks) / (duration_s / 60.0)
    print(f"Peak detection method: {method}")
    print(f"Detected R-peaks: {len(peaks)}")
    print(f"Approximate mean heart rate from peak count: {hr_bpm:.2f} bpm")

    # Ensure all values are scalar numeric where possible.
    for col in features_df.columns:
        features_df[col] = features_df[col].map(_safe_float)

    # Add useful metadata columns at the end.
    features_df["ECG_Sampling_Rate_Hz"] = FS
    features_df["ECG_Duration_s"] = duration_s
    features_df["ECG_Peak_Detection_Method"] = method

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    features_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Feature table shape: {features_df.shape}")
    print("First 20 feature columns:")
    print(list(features_df.columns[:20]))
    key_cols = [
        "HRV_Peak_Count",
        "HRV_NN_Count",
        "HRV_MeanNN",
        "HRV_SDNN",
        "HRV_RMSSD",
        "HRV_LF",
        "HRV_HF",
        "HRV_LFHF",
        "HRV_SD1",
        "HRV_SD2",
        "HRV_SampEn",
    ]
    existing = [c for c in key_cols if c in features_df.columns]
    print("Selected HRV features:")
    print(features_df[existing].to_string(index=False))
    print(f"Saved HRV analysis to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()