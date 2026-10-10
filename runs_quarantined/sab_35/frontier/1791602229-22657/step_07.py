#!/usr/bin/env python3
import neurokit2 as nk
import inspect
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

print("rsp_rrv signature and doc excerpt:")
print(inspect.signature(nk.rsp_rrv))
print((inspect.getdoc(nk.rsp_rrv) or "")[:2000].replace("\n", "\n  "))

df = pd.read_csv("benchmark/datasets/biosignals/bio_eventrelated_100hz.csv")
signals, info = nk.rsp_process(df["RSP"].values, sampling_rate=100, method="khodadad2018")

print("\nTrying nk.rsp_rrv with signals...")
try:
    rrv = nk.rsp_rrv(signals, sampling_rate=100)
    print("type", type(rrv), "shape", getattr(rrv, "shape", None))
    print("columns", list(rrv.columns) if hasattr(rrv, "columns") else None)
    print(rrv.T.to_string() if hasattr(rrv, "T") else rrv)
except Exception as e:
    print("signals error:", repr(e))

print("\nTrying nk.rsp_rrv with troughs/info...")
for arg in [info, info["RSP_Troughs"], {"RSP_Peaks": info["RSP_Troughs"]}]:
    try:
        rrv = nk.rsp_rrv(arg, sampling_rate=100)
        print("arg", type(arg), "OK shape", getattr(rrv, "shape", None))
        print(list(rrv.columns)[:20])
        print(rrv.T.to_string())
    except Exception as e:
        print("arg", type(arg), "error", repr(e))