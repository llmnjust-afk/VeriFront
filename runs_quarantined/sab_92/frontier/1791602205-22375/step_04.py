#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np


def locate_data_dir():
    candidates = [
        Path("jnmf_visualization"),
        Path("benchmark/datasets/jnmf_visualization"),
    ]
    needed = [
        "fit_result_conscientiousness_W_high.npy",
        "fit_result_conscientiousness_W_low.npy",
        "fit_result_conscientiousness_H_high.npy",
        "fit_result_conscientiousness_H_low.npy",
    ]
    for d in candidates:
        if all((d / name).exists() for name in needed):
            return d
    raise FileNotFoundError("Could not locate jnmf_visualization dataset")


def main():
    data_dir = locate_data_dir()
    out_path = Path("pred_results/jnmf_h_importances.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    W_high = np.load(data_dir / "fit_result_conscientiousness_W_high.npy")
    W_low = np.load(data_dir / "fit_result_conscientiousness_W_low.npy")
    H_high = np.load(data_dir / "fit_result_conscientiousness_H_high.npy")
    H_low = np.load(data_dir / "fit_result_conscientiousness_H_low.npy")

    print("Using data directory:", data_dir)
    print("Loaded arrays:")
    print("  W_high", W_high.shape, "sum", float(W_high.sum()))
    print("  W_low ", W_low.shape, "sum", float(W_low.sum()))
    print("  H_high", H_high.shape, "sum", float(H_high.sum()))
    print("  H_low ", H_low.shape, "sum", float(H_low.sum()))

    sum_H_high = np.sum(H_high)
    sum_H_low = np.sum(H_low)
    sum_H_both = sum_H_high + sum_H_low

    scores = {
        "common error": float(1.0 - np.inner(W_high[:, 0], W_low[:, 0])),
        "common importance": float((np.sum(H_high[:, 0]) + np.sum(H_low[:, 0])) / sum_H_both),
        "high importance": float(np.sum(H_high[:, 1]) / sum_H_high),
        "low importance": float(np.sum(H_low[:, 1]) / sum_H_low),
        "distinct error": float(np.inner(W_high[:, 1], W_low[:, 1])),
        "distinct importance": float((np.sum(H_high[:, 1]) + np.sum(H_low[:, 1])) / sum_H_both),
    }

    print("Computed scores:")
    for key, value in scores.items():
        print(f"  {key}: {value:.17g}")

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Saved JSON to {out_path}")
    print("JSON content:")
    print(out_path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()