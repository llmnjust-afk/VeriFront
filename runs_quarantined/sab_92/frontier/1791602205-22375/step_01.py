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
    print("  W_high", W_high.shape, "sum", float(W_high.sum()))
    print("  W_low ", W_low.shape, "sum", float(W_low.sum()))
    print("  H_high", H_high.shape, "sum", float(H_high.sum()))
    print("  H_low ", H_low.shape, "sum", float(H_low.sum()))

    # Columns are selected as specified in the task description.
    wh_common = W_high[:, 0]
    wl_common = W_low[:, 0]
    wh_distinct = W_high[:, 1]
    wl_distinct = W_low[:, 1]

    hh_common = H_high[:, 0]
    hl_common = H_low[:, 0]
    hh_distinct = H_high[:, 1]
    hl_distinct = H_low[:, 1]

    h_high_total = np.sum(H_high)
    h_low_total = np.sum(H_low)
    h_combined_total = h_high_total + h_low_total

    scores = {
        "common error": float(1.0 - np.inner(wh_common, wl_common)),
        "common importance": float((np.sum(hh_common) + np.sum(hl_common)) / h_combined_total),
        "high importance": float(np.sum(hh_distinct) / h_high_total),
        "low importance": float(np.sum(hl_distinct) / h_low_total),
        "distinct error": float(np.inner(wh_distinct, wl_distinct)),
        "distinct importance": float((np.sum(hh_distinct) + np.sum(hl_distinct)) / h_combined_total),
    }

    print("Computed scores:")
    for key, value in scores.items():
        print(f"  {key}: {value:.17g}")

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Saved JSON to {out_path}")


if __name__ == "__main__":
    main()