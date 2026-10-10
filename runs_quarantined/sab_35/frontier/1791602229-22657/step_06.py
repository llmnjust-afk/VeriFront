#!/usr/bin/env python3
import neurokit2 as nk
import inspect

names = [n for n in dir(nk) if "rrv" in n.lower() or ("rsp" in n.lower() and ("interval" in n.lower() or "frequency" in n.lower()))]
print("Names containing rrv or selected rsp:")
for n in names:
    print(n)

print("\nHRV functions potentially reusable on breath intervals:")
for n in ["hrv_time", "hrv_frequency", "hrv_nonlinear", "hrv"]:
    obj = getattr(nk, n, None)
    print("\n", n, obj is not None)
    if obj is not None:
        print(inspect.signature(obj))
        doc = inspect.getdoc(obj) or ""
        print(doc[:800].replace("\n", "\n  "))

print("\nrsp_intervalrelated full columns test")
import pandas as pd
df = pd.read_csv("benchmark/datasets/biosignals/bio_eventrelated_100hz.csv")
signals, info = nk.rsp_process(df["RSP"].values, sampling_rate=100)
try:
    out = nk.rsp_intervalrelated(signals, sampling_rate=100)
    print(out.shape)
    print(list(out.columns))
    print(out.T.to_string())
except Exception as e:
    print("ERROR", repr(e))