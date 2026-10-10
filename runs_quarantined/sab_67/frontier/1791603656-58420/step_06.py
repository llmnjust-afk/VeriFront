import os
from pathlib import Path
import numpy as np
import pandas as pd

def get_syllogistic_constants(model_dfs):
    try:
        import ccobra
        print("Using ccobra syllogistic constants.")
        return list(ccobra.syllogistic.SYLLOGISMS), list(ccobra.syllogistic.RESPONSES)
    except Exception as e:
        print("ccobra import failed, using fallback constants:", repr(e))
        # Standard ccobra syllogistic ordering: 16 moods x 4 figures, and 9 response alternatives.
        moods = ["AA", "AI", "AE", "AO",
                 "IA", "II", "IE", "IO",
                 "EA", "EI", "EE", "EO",
                 "OA", "OI", "OE", "OO"]
        syllogisms = [mood + str(fig) for mood in moods for fig in range(1, 5)]
        responses = ["Aac", "Aca", "Iac", "Ica", "Eac", "Eca", "Oac", "Oca", "NVC"]
        # Validate against input coverage.
        all_syl = set().union(*(set(df["Syllogism"].astype(str)) for df in model_dfs))
        if set(syllogisms) != all_syl:
            print("Fallback syllogism mismatch.")
            print("Missing in fallback:", sorted(all_syl - set(syllogisms))[:20])
            print("Missing in data:", sorted(set(syllogisms) - all_syl)[:20])
            # Last-resort use the first dataframe order if it has 64 rows.
            syllogisms = list(model_dfs[0]["Syllogism"].astype(str))
        return syllogisms, responses

def main():
    base = Path("benchmark/datasets/CogSci_pattern_high_sim_data")
    out_dir = Path("pred_results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "CogSci_pattern_high_sim_data_pred.csv"

    properties = ["conscientiousness", "openness"]
    model_names = ["Atmosphere", "Conversion", "Matching", "MMT", "PHM", "PSYCOP", "VerbalModels"]
    csv_paths = [base / f"{name}.csv" for name in model_names]

    print("Base:", base.resolve())
    print("Output:", out_path.resolve())
    for p in csv_paths + [base / f"fit_result_{prop}_W_high.npy" for prop in properties]:
        print("Input exists:", p, p.exists(), p.stat().st_size if p.exists() else None)

    model_dfs = [pd.read_csv(path) for path in csv_paths]
    syllogisms, responses = get_syllogistic_constants(model_dfs)
    print("Number of syllogisms:", len(syllogisms))
    print("Number of responses:", len(responses))
    print("First syllogisms:", syllogisms[:8])
    print("Responses:", responses)

    high_models = {}
    for prop in properties:
        W_high = np.load(base / f"fit_result_{prop}_W_high.npy")
        high_pattern = W_high[:, 1]
        print(f"\nTrait {prop}: W_high shape {W_high.shape}; high_pattern norm {np.linalg.norm(high_pattern):.12g}")

        high_models[prop] = {}
        for model_name, model_df in zip(model_names, model_dfs):
            model_lookup = dict(zip(model_df["Syllogism"].astype(str), model_df["Prediction"].astype(str)))
            model_vec = np.zeros(len(syllogisms) * len(responses), dtype=float)

            for i, syl in enumerate(syllogisms):
                if syl not in model_lookup:
                    raise KeyError(f"{model_name} has no prediction for syllogism {syl}")
                preds = [pred for pred in model_lookup[syl].split(";") if pred != ""]
                if not preds:
                    raise ValueError(f"{model_name} has empty prediction for syllogism {syl}")
                for pred in preds:
                    if pred not in responses:
                        raise ValueError(f"Unknown response {pred!r} in {model_name}, syllogism {syl}")
                    pred_idx = responses.index(pred)
                    model_vec[i * len(responses) + pred_idx] += 1.0 / len(preds)

            if len(model_vec) != len(high_pattern):
                raise ValueError(f"Vector length mismatch for {prop}/{model_name}: model {len(model_vec)}, pattern {len(high_pattern)}")

            dot_prod_high = float(np.dot(high_pattern, model_vec))
            norm_high = float(np.linalg.norm(high_pattern) * np.linalg.norm(model_vec))
            score = dot_prod_high / norm_high
            high_models[prop][model_name] = score
            print(f"  {model_name:13s} dot={dot_prod_high:.12g} norm={norm_high:.12g} cosine={score:.12g}")

    result_df = pd.DataFrame(high_models)
    result_df.to_csv(out_path)
    print("\nSaved result:")
    print(result_df.to_string())
    print("\nCSV content:")
    print(out_path.read_text())

if __name__ == "__main__":
    main()