#!/usr/bin/env python3
import os
import pickle
from pathlib import Path

import pandas as pd


def load_dataframe(path: Path) -> pd.DataFrame:
    """Load the questionnaire pickle as a pandas DataFrame."""
    obj = pd.read_pickle(path)
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    # Fallback for unusual pickle payloads
    with open(path, "rb") as f:
        obj = pickle.load(f)
    if not isinstance(obj, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame in {path}, got {type(obj)!r}")
    return obj.copy()


def main():
    input_path = Path("biopsykit_questionnaire_data/questionnaire_data.pkl")
    output_dir = Path("pred_results")
    output_path = output_dir / "questionnaire_pred.csv"

    df = load_dataframe(input_path)

    print(f"Loaded data from: {input_path}")
    print(f"Data shape: {df.shape}")
    print(f"Columns preview: {list(df.columns[:12])}")

    required_cols = ["subject"] + [f"PSS_{i:02d}" for i in range(1, 11)]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]

    # PSS-10 scoring:
    # Perceived helplessness: items 1, 2, 3, 6, 9, 10, summed as coded.
    # Perceived self-efficacy: positive items 4, 5, 7, 8, reverse scored
    # on the 0..4 PSS response scale and then summed.
    helplessness_cols = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
    self_efficacy_cols = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

    # Validate numeric range for PSS items.
    pss_values = df[pss_cols].apply(pd.to_numeric, errors="raise")
    min_val = pss_values.min().min()
    max_val = pss_values.max().max()
    print(f"PSS item value range observed: min={min_val}, max={max_val}")
    if min_val < 0 or max_val > 4:
        raise ValueError("PSS items are expected to be coded from 0 to 4.")

    perceived_helplessness = pss_values[helplessness_cols].sum(axis=1)
    perceived_self_efficacy = (4 - pss_values[self_efficacy_cols]).sum(axis=1)
    total_pss = perceived_helplessness + perceived_self_efficacy

    result = pd.DataFrame(
        {
            "subject": df["subject"],
            "perceived_helplessness": perceived_helplessness.astype(int),
            "perceived_self_efficacy": perceived_self_efficacy.astype(int),
            "total_pss": total_pss.astype(int),
        }
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, header=False)

    print(f"Saved PSS results to: {output_path}")
    print(f"Result shape: {result.shape}")
    print("First 10 output rows:")
    print(result.head(10).to_string(index=False))
    print("Score summaries:")
    print(result[["perceived_helplessness", "perceived_self_efficacy", "total_pss"]].describe().to_string())


if __name__ == "__main__":
    main()