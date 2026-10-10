#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np


def main():
    data_dir = Path("jnmf_visualization")
    out_path = Path("pred_results/jnmf_h_importances.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    W_high = np.load(data_dir / "fit_result_conscientiousness_W_high.npy")
    W_low = np.load(data_dir / "fit_result_conscientiousness_W_low.npy")
    H_high = np.load(data_dir / "fit_result_conscientiousness_H_high.npy")
    H_low = np.load(data_dir / "fit_result_conscientiousness_H_low.npy")

    print("Loaded arrays:")
    print(f"  W_high shape: {W_high.shape}, dtype: {W_high.dtype}")
    print(f"  W_low  shape: {W_low.shape}, dtype: {W_low.dtype}")
    print(f"  H_high shape: {H_high.shape}, dtype: {H_high.dtype}")
    print(f"  H_low  shape: {H_low.shape}, dtype: {H_low.dtype}")

    # Required factors, using columns exactly as specified.
    common_error = 1.0 - float(np.inner(W_high[:, 0], W_low[:, 0]))

    common_importance = float(
        (np.sum(H_high[:, 0]) + np.sum(H_low[:, 0]))
        / (np.sum(H_high) + np.sum(H_low))
    )

    high_importance = float(np.sum(H_high[:, 1]) / np.sum(H_high))

    low_importance = float(np.sum(H_low[:, 1]) / np.sum(H_low))

    distinct_error = float(np.inner(W_high[:, 1], W_low[:, 1]))

    distinct_importance = float(
        (np.sum(H_high[:, 1]) + np.sum(H_low[:, 1]))
        / (np.sum(H_high) + np.sum(H_low))
    )

    scores = {
        "common_error": common_error,
        "common_importance": common_importance,
        "high_importance": high_importance,
        "low_importance": low_importance,
        "distinct_error": distinct_error,
        "distinct_importance": distinct_importance,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, sort_keys=True)

    print("Computed scores:")
    for key, value in scores.items():
        print(f"  {key}: {value:.17g}")

    print(f"Saved JSON to: {out_path}")


if __name__ == "__main__":
    main()