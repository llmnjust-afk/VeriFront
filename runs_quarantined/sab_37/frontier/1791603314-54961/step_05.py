import json
from pathlib import Path
import pandas as pd
import numpy as np
import importlib.util

paths = [
    Path("/data/lab/sab_data/benchmark_verified/benchmark/eval_programs/gold_results/biopsykit_cft_gold_results.json"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/scoring_rubrics/cft_rubric.json"),
    Path("/data/lab/VeriFront/runs/sab_37/frontier/1791600644-15140/pred_results/cft_pred_results.json"),
    Path("/data/lab/VeriFront/runs/sab_37/frontier/1791602009-20249/pred_results/cft_pred_results.json"),
    Path("/data/lab/gold_sanity/37/pred_results/cft_pred_results.json"),
]
for p in paths:
    print("\nPATH", p, "exists", p.exists())
    if p.exists():
        print(p.read_text()[:2000])

print("\nBioPsyKit installed?", importlib.util.find_spec("biopsykit") is not None)
if importlib.util.find_spec("biopsykit"):
    import biopsykit
    print("biopsykit version", getattr(biopsykit, "__version__", None))

# Investigate MIST3 time spacing and simple candidate metrics
xlsx = Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx")
df = pd.read_excel(xlsx, sheet_name="MIST3")
df["elapsed_s"] = (df["time"] - df["time"].iloc[0]).dt.total_seconds()
print("\nMIST3 shape", df.shape)
print("start", df["time"].iloc[0], "end", df["time"].iloc[-1], "duration", df["elapsed_s"].iloc[-1])
print("HR first/last")
print(df.head(20).to_string(index=False))
print(df.tail(20).to_string(index=False))
for sec in [5,10,15,20,30,45,60]:
    print("mean first", sec, df.loc[df.elapsed_s <= sec, "Heart_Rate"].mean(), "n", (df.elapsed_s <= sec).sum())
for sec in [5,10,15,20,30,45,60]:
    print("mean last", sec, df.loc[df.elapsed_s >= df.elapsed_s.iloc[-1]-sec, "Heart_Rate"].mean(), "n", (df.elapsed_s >= df.elapsed_s.iloc[-1]-sec).sum())
print("min row", df.loc[df.Heart_Rate.idxmin()].to_dict())
print("max row", df.loc[df.Heart_Rate.idxmax()].to_dict())