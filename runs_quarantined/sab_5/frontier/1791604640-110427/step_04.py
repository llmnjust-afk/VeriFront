#!/usr/bin/env python3
import os
from pathlib import Path
import json
import pandas as pd

base = Path("benchmark/datasets/dkpes")
print("DKPES base:", base, "exists:", base.exists(), "resolve:", base.resolve() if base.exists() else None)
print("Files:", os.listdir(base) if base.exists() else None)

paths = {
    "train": base / "dkpes_train.csv",
    "test": base / "dkpes_test.csv",
}
summary = {}
for name, path in paths.items():
    print(f"\n--- {name}: {path} ---")
    df = pd.read_csv(path)
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print("head:")
    print(df.head(10).to_string())
    print("tail:")
    print(df.tail(3).to_string())
    print("dtypes:")
    print(df.dtypes.to_string())
    print("missing values:")
    print(df.isna().sum().to_string())
    summary[name] = {
        "path": str(path),
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing": {c: int(v) for c, v in df.isna().sum().items()},
    }
    if "Signal-inhibition" in df.columns:
        y = pd.to_numeric(df["Signal-inhibition"], errors="coerce")
        print("Signal-inhibition summary:")
        print(y.describe().to_string())
        print("quantiles:")
        print(y.quantile([0, .01, .05, .1, .2, .25, .3, .4, .5, .6, .7, .75, .8, .9, .95, .99, 1]).to_string())
        print("unique count:", y.nunique(), "top frequencies:")
        print(y.value_counts().head(20).to_string())
        summary[name]["signal_summary"] = y.describe().to_dict()
        summary[name]["signal_quantiles"] = y.quantile([0, .01, .05, .1, .2, .25, .3, .4, .5, .6, .7, .75, .8, .9, .95, .99, 1]).to_dict()

print("\nSearching for dkpes-related gold/eval/rubric files:")
for root in ["benchmark/gold_programs", "benchmark/eval_programs", "benchmark/scoring_rubrics"]:
    p = Path(root)
    if p.exists():
        for f in p.rglob("*"):
            if "dkpes" in f.name.lower() or "dkpes" in str(f).lower():
                print(f, "size", f.stat().st_size)
                try:
                    txt = f.read_text(errors="ignore")
                    print("--- first 4000 chars ---")
                    print(txt[:4000])
                    print("--- end preview ---")
                except Exception as e:
                    print("read error", e)

with open("dkpes_inspection_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nWrote dkpes_inspection_summary.json")