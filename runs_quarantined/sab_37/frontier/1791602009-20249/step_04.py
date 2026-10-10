import os, json, inspect
from pathlib import Path
import pandas as pd
import numpy as np

path = Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx")
if not path.exists():
    path = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/mist_hr/hr_sample_mist.xlsx")
print("Path:", path, path.exists())

xl = pd.ExcelFile(path)
print("Sheets:", xl.sheet_names)
for sh in xl.sheet_names:
    df = pd.read_excel(path, sheet_name=sh)
    print("\nSHEET", sh, "shape", df.shape)
    print("columns:", list(df.columns))
    print("head:")
    print(df.head(8).to_string(index=False))
    print("tail:")
    print(df.tail(3).to_string(index=False))
    if "time" in df.columns and "Heart_Rate" in df.columns:
        times = pd.to_datetime(df["time"])
        rel = (times - times.iloc[0]).dt.total_seconds()
        print("duration s:", rel.iloc[-1], "n:", len(df), "median dt:", np.median(np.diff(rel)))
        print("HR stats:", df["Heart_Rate"].describe(percentiles=[.05,.25,.5,.75,.95]).to_string())

print("\nBioPsyKit import inspection:")
mods = ["biopsykit", "biopsykit.signals", "biopsykit.protocols", "biopsykit.protocols.cft", "biopsykit.utils"]
for m in mods:
    try:
        mod = __import__(m, fromlist=["*"])
        print(m, "OK", getattr(mod, "__file__", None))
        names = [n for n in dir(mod) if "cft" in n.lower() or "cold" in n.lower() or "CFT" in n or "hr" in n.lower()]
        print(" names:", names[:50])
    except Exception as e:
        print(m, "ERR", repr(e))

# Walk biopsykit package for cft references if installed
try:
    import biopsykit, pkgutil
    for importer, modname, ispkg in pkgutil.walk_packages(biopsykit.__path__, biopsykit.__name__ + "."):
        if "cft" in modname.lower() or "cold" in modname.lower():
            print("pkg:", modname, "ispkg", ispkg)
except Exception as e:
    print("walk err", e)