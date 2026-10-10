#!/usr/bin/env python3
import inspect
from biopsykit.signals.ecg import EcgProcessor
import biopsykit.signals.ecg.ecg as ecg_mod
import biopsykit.signals.ecg.plotting as plotting

print("EcgProcessor:", EcgProcessor)
print("Signature:", inspect.signature(EcgProcessor))
print("Docstring first 2000:")
print((inspect.getdoc(EcgProcessor) or "")[:2000])

print("\nEcgProcessor public methods/properties:")
for name in dir(EcgProcessor):
    if not name.startswith("_"):
        obj = getattr(EcgProcessor, name)
        print(" ", name, type(obj))
        if callable(obj):
            try:
                print("    sig:", inspect.signature(obj))
            except Exception:
                pass
            doc = inspect.getdoc(obj) or ""
            if doc:
                print("    doc:", doc[:300].replace("\n", " "))

print("\nPlotting funcs:")
for name in ["ecg_plot", "hr_plot", "hr_distribution_plot", "rr_distribution_plot"]:
    if hasattr(plotting, name):
        obj=getattr(plotting,name)
        print(name, inspect.signature(obj))
        print((inspect.getdoc(obj) or "")[:800].replace("\n"," "))

print("\nConstants:")
print("R_PEAK_DATAFRAME_COLUMNS", ecg_mod.R_PEAK_DATAFRAME_COLUMNS)
print("ECG_RESULT_DATAFRAME_COLUMNS", ecg_mod.ECG_RESULT_DATAFRAME_COLUMNS)
print("HEART_RATE_DATAFRAME_COLUMNS", ecg_mod.HEART_RATE_DATAFRAME_COLUMNS)