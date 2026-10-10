import os, glob
import numpy as np
import pandas as pd

# Search for task-specific gold/eval/source files mentioning CogSci_pattern_high_sim
matches = []
for root, dirs, files in os.walk("benchmark"):
    # skip huge dataset subtrees not needed after shallow? keep okay
    for f in files:
        path = os.path.join(root, f)
        if f.endswith((".py", ".md", ".txt", ".csv", ".json")):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    txt = fh.read()
                if "CogSci_pattern_high_sim" in txt or "fit_result_conscientiousness_W_high" in txt or "pattern_high" in txt:
                    matches.append(path)
            except Exception:
                pass
print("Text files mentioning task:", matches)

for path in matches[:20]:
    print("\n---", path, "---")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            txt = fh.read()
        idxs = []
        for key in ["CogSci_pattern_high_sim", "fit_result_conscientiousness_W_high", "pattern_high"]:
            i = txt.find(key)
            if i >= 0:
                idxs.append(i)
        if idxs:
            i = min(idxs)
            print(txt[max(0, i-1500):i+3000])
        else:
            print(txt[:3000])
    except Exception as e:
        print("failed:", e)

# Inspect plot data because it may show expected similarity structure/format
plot_path = "benchmark/datasets/CogSci_pattern_high_sim_plot_data/CogSci_pattern_high_sim_plot.csv"
if os.path.exists(plot_path):
    plot = pd.read_csv(plot_path)
    print("\nPlot data shape", plot.shape)
    print(plot.head(20).to_string(index=False))
    print(plot.tail(20).to_string(index=False))
    print(plot.columns.tolist())
    print(plot.describe(include="all").to_string())
else:
    print("No plot data at", plot_path)