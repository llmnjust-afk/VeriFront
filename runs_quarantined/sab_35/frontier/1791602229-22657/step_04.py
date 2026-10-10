#!/usr/bin/env python3
import neurokit2 as nk
import inspect

print("NeuroKit2 version:", nk.__version__)
for name in ["rsp_clean", "rsp_peaks", "rsp_rate", "rsp_process", "rsp_intervalrelated", "rsp_eventrelated", "rsp_symmetry", "rsp_rrv"]:
    obj = getattr(nk, name, None)
    print("\n", name, "exists:", obj is not None)
    if obj is not None:
        try:
            print(inspect.signature(obj))
        except Exception as e:
            print("signature error:", e)
        doc = inspect.getdoc(obj) or ""
        print(doc[:1000].replace("\n", "\n  "))