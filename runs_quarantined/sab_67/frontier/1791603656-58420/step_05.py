from pathlib import Path
import pandas as pd
import numpy as np

cwd = Path.cwd()
paths = [
    cwd/"benchmark/gold_programs/CogSci_pattern_high_sim.py",
    cwd/"benchmark/eval_programs/CogSci_pattern_high_sim_eval.py",
    cwd/"benchmark/eval_programs/gold_results/CogSci_pattern_high_sim_data_gold.csv",
]
for p in paths:
    print("\n---", p.relative_to(cwd), "---")
    if p.suffix == ".py":
        print(p.read_text(errors="replace"))
    elif p.suffix == ".csv":
        df = pd.read_csv(p)
        print("shape", df.shape)
        print(df.to_string(index=False))

base = cwd/"benchmark/datasets/CogSci_pattern_high_sim_data"
print("\nInspect NPY arrays:")
for npy in sorted(base.glob("*.npy")):
    arr = np.load(npy)
    print(npy.name, "shape", arr.shape, "dtype", arr.dtype, "min/max/sum", arr.min(), arr.max(), arr.sum())
    print(arr[:5, :10] if arr.ndim == 2 else arr[:20])

print("\nInspect all CSVs full:")
for csv in sorted(base.glob("*.csv")):
    df = pd.read_csv(csv)
    print("\n", csv.name, df.shape)
    print(df.to_string(index=False))