#!/usr/bin/env python3
import inspect
from pathlib import Path
import pandas as pd
import neurokit2 as nk

data_path = Path("pred_results/data_path.txt").read_text().strip()
df = pd.read_csv(data_path)
rsp = df["RSP"].astype(float).values
fs = 100
print("Data path:", data_path)
print("RSP length:", len(rsp), "duration_s:", len(rsp)/fs)

print("\nNeuroKit2 version:", getattr(nk, "__version__", "unknown"))
for name in ["rsp_clean", "rsp_peaks", "rsp_process", "rsp_rate", "rsp_intervalrelated", "rsp_analyze", "hrv_time", "hrv_frequency", "hrv_nonlinear"]:
    obj = getattr(nk, name, None)
    print(f"\n{name}: {obj}")
    if obj is not None:
        try:
            print(str(inspect.signature(obj)))
        except Exception as e:
            print("signature error:", e)
        doc = inspect.getdoc(obj)
        if doc:
            print("doc first lines:", "\n".join(doc.splitlines()[:8]))

# Try standard rsp_process to inspect outputs
try:
    signals, info = nk.rsp_process(rsp, sampling_rate=fs)
    print("\nrsp_process signals shape:", signals.shape)
    print("signals columns:", list(signals.columns))
    print("info keys:", list(info.keys()))
    for k, v in info.items():
        try:
            print("info", k, "len", len(v), "first10", list(v[:10]) if hasattr(v, "__getitem__") else v)
        except Exception:
            print("info", k, type(v), v)
    print(signals.head().to_string())
    print(signals.describe().to_string())
except Exception as e:
    print("rsp_process failed:", repr(e))