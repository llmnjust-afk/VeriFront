import os, glob
import numpy as np
import pandas as pd

base = "benchmark/datasets/CogSci_pattern_high_sim_data"
print("Current pred_results:", sorted(os.listdir("pred_results")) if os.path.exists("pred_results") else "no dir")

# inspect benchmark files that may specify expected output format or related scripts
print("\nBenchmark tree (limited):")
for root, dirs, files in os.walk("benchmark"):
    depth = root.count(os.sep)
    if depth <= 3:
        print(root, "dirs=", dirs[:10], "files=", files[:20])

# Detailed numeric summaries of pattern matrices
for trait in ["conscientiousness", "openness"]:
    fn = f"fit_result_{trait}_W_high.npy"
    W = np.load(os.path.join(base, fn))
    print(f"\n{trait} W shape {W.shape}")
    col_sums = W.sum(axis=0)
    col_norms = np.linalg.norm(W, axis=0)
    print("col_sums:", col_sums)
    print("col_norms:", col_norms)
    print("col_max:", W.max(axis=0), "col_argmax:", W.argmax(axis=0))
    print("nonzero >1e-12:", (W > 1e-12).sum(axis=0))
    print("column cosine:", float(W[:,0].dot(W[:,1])/(col_norms[0]*col_norms[1])))
    print("row sum min/max/mean:", W.sum(axis=1).min(), W.sum(axis=1).max(), W.sum(axis=1).mean())

# Build model vectors with likely syllogism-major/token order and inspect similarities under possible aggregation
tokens = ['Aac', 'Aca', 'Eac', 'Eca', 'Iac', 'Ica', 'NVC', 'Oac', 'Oca']
model_files = sorted([f for f in os.listdir(base) if f.endswith(".csv")])
print("\nTokens:", tokens)
for fn in model_files:
    df = pd.read_csv(os.path.join(base, fn))
    v = []
    for pred in df["Prediction"].astype(str):
        predset = set(x for x in pred.split(";") if x)
        v.extend([1.0 if t in predset else 0.0 for t in tokens])
    v = np.array(v)
    print(fn, "vector length", len(v), "ones", int(v.sum()), "norm", np.linalg.norm(v))
    for trait in ["conscientiousness", "openness"]:
        W = np.load(os.path.join(base, f"fit_result_{trait}_W_high.npy"))
        sims = (W.T @ v) / (np.linalg.norm(W, axis=0) * np.linalg.norm(v))
        print(" ", trait, "sims cols", sims, "max", sims.max(), "mean", sims.mean(), "sum-pattern cos", W.sum(axis=1).dot(v)/(np.linalg.norm(W.sum(axis=1))*np.linalg.norm(v)))