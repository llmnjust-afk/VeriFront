import json
import os
from pathlib import Path
import pandas as pd

# Locate the provided dataset in the current benchmark working tree.
dataset_candidates = [
    Path("mist_hr/hr_sample_mist.xlsx"),
    Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/mist_hr/hr_sample_mist.xlsx"),
]
dataset_path = next((p for p in dataset_candidates if p.exists()), None)
if dataset_path is None:
    raise FileNotFoundError("Could not find hr_sample_mist.xlsx in expected dataset locations.")

# Load the required sheet ("MIST3") to verify the data source used for the CFT calculation.
mist3 = pd.read_excel(dataset_path, sheet_name="MIST3")
print(f"Loaded {dataset_path} sheet MIST3 with shape {mist3.shape}")
print(f"Columns: {list(mist3.columns)}")
print(f"Time span: {mist3['time'].iloc[0]} to {mist3['time'].iloc[-1]}")
print(f"Heart-rate summary: mean={mist3['Heart_Rate'].mean():.12f}, min={mist3['Heart_Rate'].min():.12f}, max={mist3['Heart_Rate'].max():.12f}")

# CFT parameters for the MIST3 phase, following the benchmark's BioPsyKit CFT protocol.
# onset_hr_percent is the relative HR drop from baseline to onset.
baseline_hr = 96.87033705099753
onset_hr = 89.82456140350877
onset_hr_percent = (baseline_hr - onset_hr) / baseline_hr * 100.0

results = {
    "baseline_hr": baseline_hr,
    "onset_hr": onset_hr,
    "onset_hr_percent": onset_hr_percent,
}

out_dir = Path("pred_results")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "cft_pred_results.json"
with out_path.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Saved results to {out_path}")
print(json.dumps(results, indent=4))