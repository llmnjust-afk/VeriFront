import os
from pathlib import Path
import pandas as pd
import numpy as np

candidates = [
    Path("mist_hr/hr_sample_mist.xlsx"),
    Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/mist_hr/hr_sample_mist.xlsx"),
]
path = next((p for p in candidates if p.exists()), None)
print("Selected path:", path)
print("Exists:", path.exists(), "Size:", path.stat().st_size)

xl = pd.ExcelFile(path)
print("Sheets:", xl.sheet_names)

sheet = "MIST3"
df = pd.read_excel(path, sheet_name=sheet)
print("Sheet shape:", df.shape)
print("Columns:", list(df.columns))
print("Head 5:")
print(df.head().to_string(index=False))
print("Tail 5:")
print(df.tail().to_string(index=False))
print("Dtypes:")
print(df.dtypes.to_string())
print("Describe:")
print(df.describe(percentiles=[0.01,0.05,0.25,0.5,0.75,0.95,0.99]).to_string())

# sampling info
t = pd.to_numeric(df["timestamps"], errors="coerce").to_numpy()
dt = np.diff(t)
print("timestamp min/max/duration:", np.nanmin(t), np.nanmax(t), np.nanmax(t)-np.nanmin(t))
print("dt stats:", pd.Series(dt).describe(percentiles=[0.01,0.05,0.5,0.95,0.99]).to_string())
print("estimated fs median:", 1/np.nanmedian(dt))

# Inspect all sheets names/shapes briefly
for sh in xl.sheet_names:
    d = pd.read_excel(path, sheet_name=sh, nrows=5)
    print("brief", sh, d.shape, list(d.columns), d.head(1).to_dict(orient="records"))