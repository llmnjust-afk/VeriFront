#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
import neurokit2 as nk
from scipy import signal

fs = 100
data_path = Path("pred_results/data_path.txt").read_text().strip()
df = pd.read_csv(data_path)
rsp = df["RSP"].astype(float).to_numpy()

print("Loaded:", data_path, "shape", df.shape)
print("Duration (s):", len(rsp)/fs)

# Clean and detect respiration extrema with NeuroKit2
cleaned = nk.rsp_clean(rsp, sampling_rate=fs, method="khodadad2018")
signals, info = nk.rsp_peaks(cleaned, sampling_rate=fs, method="khodadad2018")
print("rsp_peaks signal columns:", list(signals.columns))
print("rsp_peaks info keys:", list(info.keys()))
for k, v in info.items():
    arr = np.asarray(v)
    print(k, "n=", len(arr), "first=", arr[:10].tolist() if arr.ndim > 0 else arr)

peaks = np.asarray(info.get("RSP_Peaks", []), dtype=int)        # exhalation maxima per NK doc
troughs = np.asarray(info.get("RSP_Troughs", []), dtype=int)    # inhalation onsets/minima per NK doc

# Respiratory rate signal based on troughs (inhalation minima/onsets)
rate = nk.rsp_rate(cleaned, troughs=troughs, sampling_rate=fs, method="trough")
print("Rate length:", len(rate), "mean:", float(np.nanmean(rate)), "std:", float(np.nanstd(rate)))
print("Peaks count:", len(peaks), "Troughs count:", len(troughs))
print("Peak times first 10:", (peaks[:10]/fs).round(3).tolist())
print("Trough times first 10:", (troughs[:10]/fs).round(3).tolist())

# Try NeuroKit interval-related built-in features
try:
    proc, proc_info = nk.rsp_process(rsp, sampling_rate=fs, method="khodadad2018")
    interval = nk.rsp_intervalrelated(proc, sampling_rate=fs)
    print("rsp_intervalrelated columns:", list(interval.columns))
    print(interval.to_string())
except Exception as e:
    print("rsp_intervalrelated failed:", repr(e))
    interval = pd.DataFrame()

# Try HRV-style features on breath peaks/troughs to see usable columns
for label, indices in [("troughs", troughs), ("peaks", peaks)]:
    print("\nTesting HRV-style RRV from", label, "count", len(indices))
    for funcname in ["hrv_time", "hrv_frequency", "hrv_nonlinear"]:
        func = getattr(nk, funcname)
        try:
            out = func(indices, sampling_rate=fs, show=False)
            print(funcname, "OK shape", out.shape, "cols", list(out.columns)[:20], "...")
            print(out.iloc[:, :min(8, out.shape[1])].to_string())
        except Exception as e:
            print(funcname, "failed:", repr(e))

# Save diagnostic arrays for final computation
outdir = Path("pred_results")
outdir.mkdir(exist_ok=True)
pd.DataFrame({
    "RSP_Raw": rsp,
    "RSP_Clean": np.asarray(cleaned),
    "RSP_Rate": np.asarray(rate),
    "RSP_Peaks": signals["RSP_Peaks"].to_numpy() if "RSP_Peaks" in signals else np.zeros(len(rsp), dtype=int),
    "RSP_Troughs": signals["RSP_Troughs"].to_numpy() if "RSP_Troughs" in signals else np.zeros(len(rsp), dtype=int),
}).to_csv(outdir / "rrv_signals_debug.csv", index=False)
print("Wrote pred_results/rrv_signals_debug.csv")