#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np


def main():
    data_dir = Path("benchmark/datasets/jnmf_visualization")
    required = {
        "W_high": "fit_result_conscientiousness_W_high.npy",
        "W_low": "fit_result_conscientiousness_W_low.npy",
        "H_high": "fit_result_conscientiousness_H_high.npy",
        "H_low": "fit_result_conscientiousness_H_low.npy",
    }
    print("Working directory:", Path.cwd())
    print("Using dataset directory:", data_dir.resolve())
    for label, filename in required.items():
        p = data_dir / filename
        print(f"{label}: {p} exists={p.exists()}")

    W_high = np.load(data_dir / required["W_high"])
    W_low = np.load(data_dir / required["W_low"])
    H_high = np.load(data_dir / required["H_high"])
    H_low = np.load(data_dir / required["H_low"])

    print("Loaded shapes:")
    print(" W_high", W_high.shape)
    print(" W_low ", W_low.shape)
    print(" H_high", H_high.shape)
    print(" H_low ", H_low.shape)

    sum_H_high = np.sum(H_high)
    sum_H_low = np.sum(H_low)
    sum_H_all = sum_H_high + sum_H_low

    scores = {
        "common_error": float(1.0 - np.inner(W_high[:, 0], W_low[:, 0])),
        "common_importance": float((np.sum(H_high[:, 0]) + np.sum(H_low[:, 0])) / sum_H_all),
        "high_importance": float(np.sum(H_high[:, 1]) / sum_H_high),
        "low_importance": float(np.sum(H_low[:, 1]) / sum_H_low),
        "distinct_error": float(np.inner(W_high[:, 1], W_low[:, 1])),
        "distinct_importance": float((np.sum(H_high[:, 1]) + np.sum(H_low[:, 1])) / sum_H_all),
    }

    out_path = Path("pred_results/jnmf_h_importances.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, sort_keys=True)

    print("Intermediate sums:")
    print(" sum_H_high =", repr(float(sum_H_high)))
    print(" sum_H_low  =", repr(float(sum_H_low)))
    print(" sum_H_all  =", repr(float(sum_H_all)))
    print(" sum H_high col0 =", repr(float(np.sum(H_high[:, 0]))))
    print(" sum H_low  col0 =", repr(float(np.sum(H_low[:, 0]))))
    print(" sum H_high col1 =", repr(float(np.sum(H_high[:, 1]))))
    print(" sum H_low  col1 =", repr(float(np.sum(H_low[:, 1]))))
    print(" inner W col0 =", repr(float(np.inner(W_high[:, 0], W_low[:, 0]))))
    print(" inner W col1 =", repr(float(np.inner(W_high[:, 1], W_low[:, 1]))))

    print("Scores:")
    print(json.dumps(scores, indent=2, sort_keys=True))
    print("Saved to:", out_path.resolve())


if __name__ == "__main__":
    main()