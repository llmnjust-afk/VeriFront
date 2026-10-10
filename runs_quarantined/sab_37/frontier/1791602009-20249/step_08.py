import os, json, warnings
from pathlib import Path
import pandas as pd
import numpy as np
from biopsykit.protocols.cft import CFT

path = Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx")
if not path.exists():
    path = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/mist_hr/hr_sample_mist.xlsx")

df = pd.read_excel(path, sheet_name="MIST3")
data = df.set_index("time")
print("Loaded", path, "MIST3 shape", data.shape)
print("Time range:", data.index[0], "to", data.index[-1], "duration_s", (data.index[-1] - data.index[0]).total_seconds())
print("Columns:", list(data.columns))
print("First/last rows:")
print(data.head(3).to_string())
print(data.tail(3).to_string())

# Use BioPsyKit's default CFT structure (Baseline 60s, CFT 120s, Recovery 60s).
cft = CFT()
print("CFT structure:", cft.structure, "cft_start:", cft.cft_start, "cft_duration:", cft.cft_duration)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    res = cft.compute_cft_parameter(data, return_dict=True)
print("Warnings:", [str(x.message) for x in w])
print("Full CFT result dict:")
for k, v in res.items():
    print(f"{k}: {repr(v)}")

required = {k: float(res[k]) for k in ["baseline_hr", "onset_hr", "onset_hr_percent"]}
print("Required result:")
print(json.dumps(required, indent=2))

# Also manually verify the BioPsyKit definitions from data intervals
bl_end = data.index[0] + pd.Timedelta(seconds=cft.cft_start)
cft_start_time = data.index[0] + pd.Timedelta(seconds=cft.cft_start)
cft_end_time = cft_start_time + pd.Timedelta(seconds=cft.cft_duration)
baseline_interval = data.loc[data.index[0]:bl_end]
cft_interval = data.loc[cft_start_time:cft_end_time]
print("Manual baseline n", len(baseline_interval), "mean", baseline_interval["Heart_Rate"].mean())
print("CFT interval n", len(cft_interval), "start", cft_interval.index[0], "end", cft_interval.index[-1])
print("CFT interval first HR", cft_interval["Heart_Rate"].iloc[0], "percent vs baseline", cft_interval["Heart_Rate"].iloc[0] / baseline_interval["Heart_Rate"].mean() * 100)

# Save required JSON file
out_dir = Path("pred_results")
out_dir.mkdir(exist_ok=True)
out_path = out_dir / "cft_pred_results.json"
with out_path.open("w") as f:
    json.dump(required, f, indent=2)
print("Saved:", out_path, "exists:", out_path.exists(), "content:")
print(out_path.read_text())