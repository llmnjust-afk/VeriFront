#!/usr/bin/env python3
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from biopsykit.signals.ecg import EcgProcessor

warnings.filterwarnings("ignore", category=FutureWarning)

# Paths
data_dir = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/ecg_processing_data")
out_dir = Path("pred_results")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "ecg_processing_vis1_pred_result.png"

# Load data
ecg_raw_df = pd.read_pickle(data_dir / "ecg_data.pkl")
fs = float((data_dir / "sampling_rate.txt").read_text().strip())

print(f"Loaded ECG data: shape={ecg_raw_df.shape}, sampling_rate={fs} Hz")
print(f"Time span: {ecg_raw_df.index[0]} to {ecg_raw_df.index[-1]} ({len(ecg_raw_df)/fs:.2f} s)")

# Process ECG: filtering, R peak detection, and outlier correction
processor = EcgProcessor(ecg_raw_df, sampling_rate=fs)
processor.ecg_process(outlier_correction="all", errors="warn")

ecg_result = processor.ecg_result["Data"].copy()
rpeaks = processor.rpeaks["Data"].copy()
heart_rate = processor.heart_rate["Data"].copy()

print("ECG result columns:", list(ecg_result.columns))
print("R-peak columns:", list(rpeaks.columns))
print("Heart-rate columns:", list(heart_rate.columns))
print(f"Detected/corrected R peaks: {len(rpeaks)}")

# Build relative time axes in minutes for plotting
start_time = ecg_result.index[0]
t_min = (ecg_result.index - start_time).total_seconds().to_numpy() / 60.0
r_t_min = (rpeaks.index - start_time).total_seconds().to_numpy() / 60.0
hr_t_min = (heart_rate.index - start_time).total_seconds().to_numpy() / 60.0

# Select useful columns robustly
raw_col = "ECG_Raw" if "ECG_Raw" in ecg_result.columns else ecg_result.columns[0]
clean_col = "ECG_Clean" if "ECG_Clean" in ecg_result.columns else raw_col
hr_col = "Heart_Rate" if "Heart_Rate" in heart_rate.columns else heart_rate.columns[0]

# R-peak amplitudes from the cleaned ECG, using nearest timestamps
clean_at_rpeaks = ecg_result[clean_col].reindex(rpeaks.index, method="nearest").to_numpy()
raw_at_rpeaks = ecg_result[raw_col].reindex(rpeaks.index, method="nearest").to_numpy()

# RR intervals from corrected R-peak timestamps; heart rate already reflects correction
rr_ms = np.diff(rpeaks.index.view("int64")) / 1e6
rr_t_min = r_t_min[1:]

# Try to identify outlier/correction indicators, if BioPsyKit exposes them
outlier_cols = [c for c in rpeaks.columns if "outlier" in c.lower() or "artifact" in c.lower()]
quality_col = "R_Peak_Quality" if "R_Peak_Quality" in rpeaks.columns else None
low_quality_mask = None
if quality_col:
    q = pd.to_numeric(rpeaks[quality_col], errors="coerce")
    # Mark the lowest-quality 5% as a visual diagnostic if no explicit outlier column exists.
    low_quality_mask = q <= q.quantile(0.05)
    print(f"R-peak quality: mean={q.mean():.4f}, min={q.min():.4f}, 5th percentile={q.quantile(0.05):.4f}")

explicit_outlier_count = 0
if outlier_cols:
    for c in outlier_cols:
        vals = rpeaks[c]
        if vals.dtype == bool:
            explicit_outlier_count += int(vals.sum())
        else:
            explicit_outlier_count += int(pd.to_numeric(vals, errors="coerce").fillna(0).astype(bool).sum())
print(f"Explicit outlier/artifact columns: {outlier_cols}; explicit marked count={explicit_outlier_count}")

hr_vals = pd.to_numeric(heart_rate[hr_col], errors="coerce")
print(f"Heart rate after correction: mean={hr_vals.mean():.2f} bpm, median={hr_vals.median():.2f} bpm, range=({hr_vals.min():.2f}, {hr_vals.max():.2f}) bpm")
print(f"RR intervals after correction: mean={np.nanmean(rr_ms):.1f} ms, median={np.nanmedian(rr_ms):.1f} ms, range=({np.nanmin(rr_ms):.1f}, {np.nanmax(rr_ms):.1f}) ms")

# Downsample dense full-length traces for clear overview plotting
max_points = 12000
step = max(1, int(np.ceil(len(ecg_result) / max_points)))
ds = slice(None, None, step)

# Zoom window: first 20 seconds after recording start
zoom_seconds = 20
zoom_mask = t_min <= zoom_seconds / 60.0
r_zoom_mask = r_t_min <= zoom_seconds / 60.0

# Create figure
plt.style.use("seaborn-v0_8-whitegrid")
fig, axes = plt.subplots(
    4, 1, figsize=(16, 11), sharex=False,
    gridspec_kw={"height_ratios": [2.0, 2.2, 1.4, 1.4]}
)

# Panel 1: full raw/clean overview with detected R-peaks
ax = axes[0]
ax.plot(t_min[ds], ecg_result[raw_col].to_numpy()[ds], color="0.72", linewidth=0.6, label="Raw ECG")
ax.plot(t_min[ds], ecg_result[clean_col].to_numpy()[ds], color="#1f77b4", linewidth=0.8, label="Cleaned ECG")
ax.scatter(r_t_min, clean_at_rpeaks, s=8, color="#d62728", alpha=0.75, label=f"R peaks (n={len(rpeaks)})", zorder=3)
ax.set_title("ECG processing overview: cleaned ECG with corrected R-peak detections")
ax.set_ylabel("Amplitude")
ax.set_xlim(t_min[0], t_min[-1])
ax.legend(loc="upper right", ncol=3, fontsize=9)

# Panel 2: zoomed view
ax = axes[1]
ax.plot(t_min[zoom_mask], ecg_result.loc[zoom_mask, raw_col], color="0.75", linewidth=0.8, label="Raw ECG")
ax.plot(t_min[zoom_mask], ecg_result.loc[zoom_mask, clean_col], color="#1f77b4", linewidth=1.1, label="Cleaned ECG")
ax.scatter(r_t_min[r_zoom_mask], clean_at_rpeaks[r_zoom_mask], s=40, color="#d62728", edgecolor="white", linewidth=0.5, label="R peaks", zorder=4)
ax.set_title(f"Detailed view of first {zoom_seconds} seconds")
ax.set_ylabel("Amplitude")
ax.set_xlim(0, zoom_seconds / 60.0)
ax.legend(loc="upper right", fontsize=9)

# Panel 3: heart rate after outlier correction
ax = axes[2]
ax.plot(hr_t_min, hr_vals.to_numpy(), color="#2ca02c", linewidth=1.2)
ax.axhline(hr_vals.median(), color="black", linestyle="--", linewidth=0.9, alpha=0.7, label=f"Median {hr_vals.median():.1f} bpm")
ax.set_title("Instantaneous heart rate after R-peak outlier correction")
ax.set_ylabel("Heart rate [bpm]")
ax.set_xlim(t_min[0], t_min[-1])
ax.legend(loc="upper right", fontsize=9)

# Panel 4: RR intervals and quality/outlier diagnostic
ax = axes[3]
ax.plot(rr_t_min, rr_ms, color="#9467bd", linewidth=0.9, marker=".", markersize=3, label="RR interval")
if low_quality_mask is not None and len(low_quality_mask) > 1:
    lowq_for_rr = low_quality_mask.to_numpy()[1:]
    ax.scatter(rr_t_min[lowq_for_rr], rr_ms[lowq_for_rr], s=28, color="#ff7f0e", label="Lowest 5% R-peak quality", zorder=4)
ax.axhline(np.nanmedian(rr_ms), color="black", linestyle="--", linewidth=0.9, alpha=0.7, label=f"Median {np.nanmedian(rr_ms):.0f} ms")
ax.set_title("Corrected beat-to-beat RR intervals")
ax.set_xlabel("Time since start [min]")
ax.set_ylabel("RR interval [ms]")
ax.set_xlim(t_min[0], t_min[-1])
ax.legend(loc="upper right", fontsize=9)

fig.suptitle(
    f"ECG R-peak detection and outlier-corrected rhythm summary | fs={fs:g} Hz | duration={len(ecg_result)/fs/60:.2f} min",
    fontsize=15,
    y=0.995
)
fig.tight_layout(rect=[0, 0, 1, 0.975])
fig.savefig(out_file, dpi=180, bbox_inches="tight")
plt.close(fig)

print(f"Saved figure to: {out_file}")
print(f"Output exists: {out_file.exists()}, size={out_file.stat().st_size if out_file.exists() else 0} bytes")