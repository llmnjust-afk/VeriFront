#!/usr/bin/env python3
import pickle
from pathlib import Path

import pandas as pd


def find_input_file() -> Path:
    candidates = [
        Path("biopsykit_questionnaire_data/questionnaire_data.pkl"),
        Path("benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl"),
    ]
    for p in candidates:
        if p.exists():
            return p
    found = list(Path(".").rglob("questionnaire_data.pkl"))
    if found:
        return found[0]
    raise FileNotFoundError("Could not find questionnaire_data.pkl")


def load_dataframe(path: Path) -> pd.DataFrame:
    obj = pd.read_pickle(path)
    if not isinstance(obj, pd.DataFrame):
        with open(path, "rb") as f:
            obj = pickle.load(f)
    if not isinstance(obj, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(obj)!r}")
    return obj.copy()


def main():
    input_path = find_input_file()
    output_path = Path("pred_results/questionnaire_pred.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_dataframe(input_path)
    print(f"Loaded input: {input_path}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns[:15])}")

    required_cols = ["subject"] + [f"PSS_{i:02d}" for i in range(1, 11)]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
    pss = df[pss_cols].apply(pd.to_numeric, errors="raise")

    print("PSS first rows:")
    print(pd.concat([df[["subject"]], pss], axis=1).head().to_string(index=False))
    print(f"PSS range: {pss.min().min()} to {pss.max().max()}")

    # BioPsyKit/Cohen PSS-10 subscales:
    # - helplessness: negative items 1, 2, 3, 6, 9, 10, as coded
    # - self-efficacy: positive items 4, 5, 7, 8, reverse-scored (0..4 -> 4..0)
    helplessness_cols = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
    self_efficacy_cols = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

    perceived_helplessness = pss[helplessness_cols].sum(axis=1)
    perceived_self_efficacy = (4 - pss[self_efficacy_cols]).sum(axis=1)
    total = perceived_helplessness + perceived_self_efficacy

    result = pd.DataFrame({
        "subject": df["subject"].astype(str),
        "perceived_helplessness": perceived_helplessness.astype(int),
        "perceived_self_efficacy": perceived_self_efficacy.astype(int),
        "total_pss": total.astype(int),
    })

    result.to_csv(output_path, index=False, header=False)

    print(f"Saved: {output_path.resolve()}")
    print(f"Output shape: {result.shape}")
    print("First 12 result rows:")
    print(result.head(12).to_string(index=False))
    print("Summary:")
    print(result[["perceived_helplessness", "perceived_self_efficacy", "total_pss"]].describe().to_string())
    print("Output file preview:")
    print(output_path.read_text().splitlines()[:5])


if __name__ == "__main__":
    main()