#!/usr/bin/env python3
from pathlib import Path
import json
import os

import numpy as np


def find_dataset_dir():
    expected = [
        "fit_result_conscientiousness_W_high.npy",
        "fit_result_conscientiousness_W_low.npy",
        "fit_result_conscientiousness_H_high.npy",
        "fit_result_conscientiousness_H_low.npy",
    ]

    candidates = []
    search_roots = [Path.cwd(), Path.cwd().parent, Path("/data/lab/VeriFront")]
    for root in search_roots:
        if root.exists():
            try:
                for p in root.rglob("jnmf_visualization"):
                    if p.is_dir() and all((p / name).exists() for name in expected):
                        candidates.append(p)
            except PermissionError:
                pass

    # Also check direct common locations without expensive recursion assumptions.
    for p in [
        Path("jnmf_visualization"),
        Path("../jnmf_visualization"),
        Path("../../jnmf_visualization"),
        Path("/data/lab/VeriFront/jnmf_visualization"),
        Path("/data/lab/VeriFront/datasets/jnmf_visualization"),
    ]:
        if p.is_dir() and all((p / name).exists() for name in expected):
            candidates.append(p.resolve())

    unique = []
    seen = set()
    for c in candidates:
        rc = c.resolve()
        if rc not in seen:
            seen.add(rc)
            unique.append(rc)

    print("Current working directory:", Path.cwd())
    print("Directory listing of cwd:", [x.name for x in Path.cwd().iterdir()])
    print("Found dataset candidates:", [str(x) for x in unique])

    if not unique:
        raise FileNotFoundError("Could not locate jnmf_visualization directory containing required .npy files.")
    return unique[0]


def main():
    data_dir = find_dataset_dir()
    out_path = Path("pred_results/jnmf_h_importances.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    W_high = np.load(data_dir / "fit_result_conscientiousness_W_high.npy")
    W_low = np.load(data_dir / "fit_result_conscientiousness_W_low.npy")
    H_high = np.load(data_dir / "fit_result_conscientiousness_H_high.npy")
    H_low = np.load(data_dir / "fit_result_conscientiousness_H_low.npy")

    print("Using dataset directory:", data_dir)
    print("Loaded arrays:")
    print(f"  W_high shape: {W_high.shape}, dtype: {W_high.dtype}")
    print(f"  W_low  shape: {W_low.shape}, dtype: {W_low.dtype}")
    print(f"  H_high shape: {H_high.shape}, dtype: {H_high.dtype}")
    print(f"  H_low  shape: {H_low.shape}, dtype: {H_low.dtype}")

    scores = {
        "common_error": float(1.0 - np.inner(W_high[:, 0], W_low[:, 0])),
        "common_importance": float(
            (np.sum(H_high[:, 0]) + np.sum(H_low[:, 0]))
            / (np.sum(H_high) + np.sum(H_low))
        ),
        "high_importance": float(np.sum(H_high[:, 1]) / np.sum(H_high)),
        "low_importance": float(np.sum(H_low[:, 1]) / np.sum(H_low)),
        "distinct_error": float(np.inner(W_high[:, 1], W_low[:, 1])),
        "distinct_importance": float(
            (np.sum(H_high[:, 1]) + np.sum(H_low[:, 1]))
            / (np.sum(H_high) + np.sum(H_low))
        ),
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, sort_keys=True)

    print("Computed scores:")
    for key, value in scores.items():
        print(f"  {key}: {value:.17g}")
    print(f"Saved JSON to: {out_path.resolve()}")
    print("JSON content:")
    print(json.dumps(scores, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()