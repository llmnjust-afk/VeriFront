#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

paths = [
    Path("/data/lab/VeriFront/runs/sab_87/frontier/1791597961/step_05.py"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/gold_programs/polynomial_fit.py"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/eval_programs/eval_polynomial_fit.py"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/eval_programs/gold_results/polynomial_fit_gold.csv"),
    Path("/data/lab/VeriFront/runs/sab_87/frontier/1791597961/pred_results/polynomial_fit_pred.csv"),
]
for p in paths:
    print(f"\n=== {p} ===")
    print("exists:", p.exists(), "size:", p.stat().st_size if p.exists() else "NA")
    if not p.exists():
        continue
    if p.suffix == ".csv":
        try:
            df = pd.read_csv(p)
            print("shape:", df.shape)
            print("columns:", list(df.columns))
            print("head:")
            print(df.head(10).to_string(index=False))
            print("tail:")
            print(df.tail(5).to_string(index=False))
        except Exception as e:
            print("CSV read failed:", type(e).__name__, e)
            print(p.read_text(errors="replace")[:3000])
    else:
        txt = p.read_text(errors="replace")
        print(txt[:10000])