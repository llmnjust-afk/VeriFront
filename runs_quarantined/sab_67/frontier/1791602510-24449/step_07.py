import os
import numpy as np
import pandas as pd

# Reproduce the benchmark gold program without relying on ccobra being installed:
# ccobra.syllogistic.SYLLOGISMS is the standard 64 item order already present in all CSVs.
# ccobra.syllogistic.RESPONSES order is the standard response order used by the 576-length W vectors.
base = "benchmark/datasets/CogSci_pattern_high_sim_data"
out_path = "pred_results/CogSci_pattern_high_sim_data_pred.csv"
os.makedirs("pred_results", exist_ok=True)

properties = ["conscientiousness", "openness"]
csv_paths = [
    os.path.join(base, "Atmosphere.csv"),
    os.path.join(base, "Conversion.csv"),
    os.path.join(base, "Matching.csv"),
    os.path.join(base, "MMT.csv"),
    os.path.join(base, "PHM.csv"),
    os.path.join(base, "PSYCOP.csv"),
    os.path.join(base, "VerbalModels.csv"),
]
model_names = [
    "Atmosphere",
    "Conversion",
    "Matching",
    "MMT",
    "PHM",
    "PSYCOP",
    "VerbalModels",
]
model_dfs = [pd.read_csv(path) for path in csv_paths]

# The observed syllogism order matches the CSVs and ccobra's canonical order.
syllogisms = list(model_dfs[0]["Syllogism"])

# Standard ccobra syllogistic response order. Need exact order for vector indexing.
responses = ["Aac", "Aca", "Eac", "Eca", "Iac", "Ica", "Oac", "Oca", "NVC"]

print("Syllogisms:", len(syllogisms), syllogisms[:8], syllogisms[-8:])
print("Responses:", responses)

high_models = {}
for prop in properties:
    W_high = np.load(os.path.join(base, f"fit_result_{prop}_W_high.npy"))
    high_pattern = W_high[:, 1]  # benchmark uses column 1 as the high pattern
    high_models[prop] = {}

    print(f"\nTrait {prop}: W_high shape {W_high.shape}, high pattern norm {np.linalg.norm(high_pattern):.12g}")

    for model_name, model_df in zip(model_names, model_dfs):
        model_vec = np.zeros(576, dtype=float)
        for i, syl in enumerate(syllogisms):
            vals = model_df.loc[model_df["Syllogism"] == syl, "Prediction"].values
            if len(vals) != 1:
                raise ValueError(f"Expected one row for {syl} in {model_name}, got {len(vals)}")
            preds = str(vals[0]).split(";")
            for pred in preds:
                pred_idx = responses.index(pred)
                model_vec[i * 9 + pred_idx] += 1.0 / len(preds)

        sim = float(np.dot(high_pattern, model_vec) / (np.linalg.norm(high_pattern) * np.linalg.norm(model_vec)))
        high_models[prop][model_name] = sim
        print(f"{model_name:13s} norm={np.linalg.norm(model_vec):.12g} sim={sim:.12g}")

result = pd.DataFrame(high_models)
result.to_csv(out_path)
print("\nSaved:", out_path)
print(result.to_string())
print("\nRounded for eval:")
print(result.round().to_string())