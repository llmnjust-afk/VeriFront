#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
import neurokit2 as nk

fs = 100
data_path = Path("pred_results/data_path.txt").read_text().strip()
df = pd.read_csv(data_path)
rsp = df["RSP"].astype(float).to_numpy()

print("Loaded:", data_path, "shape", df.shape)
print("Duration (s):", len(rsp)/fs)

cleaned = nk.rsp_clean(rsp, sampling_rate=fs, method="khodadad2018")
signals, info = nk.rsp_peaks(cleaned, sampling_rate=fs, method="khodadad2018")
print("rsp_peaks signal columns:", list(signals.columns))
print("rsp_peaks info keys:", list(info.keys()))
for k, v in info.items():
    arr = np.asarray(v)
    if arr.ndim == 0:
        print(k, "scalar=", arr.item())
    else:
        print(k, "n=", len(arr), "first=", arr[:10].tolist())

peaks = np.asarray(info.get("RSP_Peaks", []), dtype=int)
troughs = np.asarray(info.get("RSP_Troughs", []), dtype=int)

rate = nk.rsp_rate(cleaned, troughs=troughs, sampling_rate=fs, method="trough")
print("Rate length:", len(rate), "mean:", float(np.nanmean(rate)), "std:", float(np.nanstd(rate)))
print("Peaks count:", len(peaks), "Troughs count:", len(troughs))
print("Peak times first 10:", (peaks[:10]/fs).round(3).tolist())
print("Trough times first 10:", (troughs[:10]/fs).round(3).tolist())

try:
    proc, proc_info = nk.rsp_process(rsp, sampling_rate=fs, method="khodadad2018")
    interval = nk.rsp_intervalrelated(proc, sampling_rate=fs)
    print("\nrsp_intervalrelated columns:", list(interval.columns))
    print(interval.to_string())
except Exception as e:
    print("\nrsp_intervalrelated failed:", repr(e))
    interval = pd.DataFrame()

for label, indices in [("troughs", troughs), ("peaks", peaks)]:
    print("\nTesting HRV-style RRV from", label, "count", len(indices))
    for funcname in ["hrv_time", "hrv_frequency", "hrv_nonlinear"]:
        func = getattr(nk, funcname)
        try:
            out = func(indices, sampling_rate=fs, show=False)
            print(funcname, "OK shape", out.shape)
            print("cols:", list(out.columns))
            print(out.to_string())
        except Exception as e:
            print(funcname, "failed:", repr(e))

outdir = Path("pred_results")
outdir.mkdir(exist_ok=True)
pd.DataFrame({
    "RSP_Raw": rsp,
    "RSP_Clean": np.asarray(cleaned),
    "RSP_Rate": np.asarray(rate),
    "RSP_Peaks": signals["RSP_Peaks"].to_numpy() if "RSP_Peaks" in signals else np.zeros(len(rsp), dtype=int),
    "RSP_Troughs": signals["RSP_Troughs"].to_numpy() if "RSP_Troughs" in signals else np.zeros(len(rsp), dtype=int),
}).to_csv(outdir / "rrv_signals_debug.csv", index=False)
print("\nWrote pred_results/rrv_signals_debug.csv")