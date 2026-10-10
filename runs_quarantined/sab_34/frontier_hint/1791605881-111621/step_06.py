#!/usr/bin/env python3
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import neurokit2 as nk

warnings.filterwarnings("default")

data_path = Path("benchmark/datasets/biosignals/bio_resting_5min_100hz.csv")
out_path = Path("pred_results/hrv_analysis_pred.csv")
out_path.parent.mkdir(parents=True, exist_ok=True)

sampling_rate = 100

print("Loading:", data_path)
df = pd.read_csv(data_path)
ecg = df["ECG"].to_numpy(dtype=float)
print("Loaded shape:", df.shape)
print("ECG length:", len(ecg), "samples; duration:", len(ecg) / sampling_rate, "s")
print("ECG finite:", np.isfinite(ecg).all(), "min:", np.nanmin(ecg), "max:", np.nanmax(ecg))

# Required by benchmark: detect peaks directly from the raw ECG exactly as provided,
# without extra cleaning or artifact correction before peak detection.
signals, info = nk.ecg_peaks(ecg, sampling_rate=sampling_rate, correct_artifacts=False)
rpeaks = np.asarray(info["ECG_R_Peaks"], dtype=int)

print("Detected R-peaks:", len(rpeaks))
print("First 10 R-peak sample indices:", rpeaks[:10].tolist())
if len(rpeaks) > 1:
    rr_ms = np.diff(rpeaks) / sampling_rate * 1000
    print("RR intervals (ms): count", len(rr_ms), "mean", float(np.mean(rr_ms)),
          "min", float(np.min(rr_ms)), "max", float(np.max(rr_ms)))

# Required by benchmark: build HRV feature table with a single nk.hrv call.
hrv_features = nk.hrv(info, sampling_rate=sampling_rate, show=False)

# Save the extracted time-, frequency-, and non-linear HRV indices.
hrv_features.to_csv(out_path, index=False)

print("HRV features shape:", hrv_features.shape)
print("Number of columns:", len(hrv_features.columns))
print("Columns:")
print(list(hrv_features.columns))
print("Saved:", out_path, "exists:", out_path.exists(), "size:", out_path.stat().st_size)
print("Preview:")
print(hrv_features.iloc[:, :min(12, hrv_features.shape[1])].to_string(index=False))