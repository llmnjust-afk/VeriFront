#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import os

base = Path("benchmark/datasets/nvc")
print("Base:", base.resolve())

# Print gold program and evaluation/rubric for this exact task
for p in [
    Path("benchmark/gold_programs/nvc_gen_ind.py"),
    Path("benchmark/eval_programs/eval_syllogistic_nvc_gen_ind.py"),
    Path("benchmark/scoring_rubrics/nvc_gen_ind_rubric.json"),
]:
    print("\n====", p, "====")
    print(p.read_text(errors="replace"))

# Preview available precomputed and model/rule files
for p in [base/"ind_data_for_plot.csv", base/"accuracies_data_for_plot.csv", base/"valid_syllogisms.csv", base/"Ragni2016.csv"]:
    print("\n==== CSV", p, "====")
    df = pd.read_csv(p)
    print("shape", df.shape)
    print("columns", list(df.columns))
    print(df.head(20).to_string(index=False))

for p in sorted((base/"scripts/indiv_table/models").glob("*.csv")):
    print("\n==== MODEL", p.name, "====")
    df = pd.read_csv(p)
    print("shape", df.shape)
    print("columns", list(df.columns))
    print(df.head(20).to_string(index=False))

for p in sorted((base/"scripts/indiv_table/rules").glob("*.py")):
    print("\n==== RULE", p.name, "====")
    print(p.read_text(errors="replace"))