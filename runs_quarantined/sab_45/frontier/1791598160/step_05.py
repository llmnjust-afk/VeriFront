#!/usr/bin/env python3
from pathlib import Path
import pickle
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
    df = load_dataframe(input_path)

    print(f"Loaded: {input_path}")
    print(f"Shape: {df.shape}")
    print(f"Index name: {df.index.name!r}")
    print(f"Index preview: {list(df.index[:5])}")
    print(f"Column preview: {list(df.columns[:12])}")

    pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
    missing_pss = [c for c in pss_cols if c not in df.columns]
    if missing_pss:
        raise KeyError(f"Missing PSS columns: {missing_pss}")

    if "subject" in df.columns:
        subjects = df["subject"].astype(str)
    else:
        subjects = pd.Series(df.index.astype(str), index=df.index, name="subject")

    pss = df[pss_cols].apply(pd.to_numeric, errors="raise")
    print("PSS data preview:")
    print(pd.concat([subjects, pss], axis=1).head().to_string(index=False))
    print(f"Observed PSS item range: {pss.min().min()} to {pss.max().max()}")

    # PSS-10 scoring (Cohen et al.): positive items 4, 5, 7, and 8 are
    # reverse-scored on the 0..4 response scale for stress-oriented scores.
    helplessness_cols = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
    self_efficacy_cols = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]

    perceived_helplessness = pss[helplessness_cols].sum(axis=1)
    perceived_self_efficacy = (4 - pss[self_efficacy_cols]).sum(axis=1)
    total_pss = perceived_helplessness + perceived_self_efficacy

    result = pd.DataFrame(
        {
            "subject": subjects.values,
            "perceived_helplessness": perceived_helplessness.astype(int).values,
            "perceived_self_efficacy": perceived_self_efficacy.astype(int).values,
            "total_pss": total_pss.astype(int).values,
        }
    )

    output_path = Path("pred_results/questionnaire_pred.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, header=False)

    print(f"Saved output file: {output_path}")
    print(f"Output shape: {result.shape}")
    print("Output preview:")
    print(result.to_string(index=False))
    print("CSV first lines:")
    print("\n".join(output_path.read_text().splitlines()[:8]))


if __name__ == "__main__":
    main()