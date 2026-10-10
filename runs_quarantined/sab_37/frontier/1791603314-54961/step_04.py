import os, json
from pathlib import Path
import pandas as pd

candidates = [
    Path("mist_hr/hr_sample_mist.xlsx"),
    Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx"),
    Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/mist_hr/hr_sample_mist.xlsx"),
]
path = next((p for p in candidates if p.exists()), None)
print("Using path:", path, "exists:", path.exists() if path else None)

xl = pd.ExcelFile(path)
print("Sheets:", xl.sheet_names)
for sheet in xl.sheet_names:
    df = pd.read_excel(path, sheet_name=sheet, nrows=8)
    print("\n---", sheet, "---")
    print("columns:", list(df.columns))
    print("head:")
    print(df.to_string(index=False))
    try:
        full = pd.read_excel(path, sheet_name=sheet)
        print("shape:", full.shape)
        print("dtypes:", full.dtypes.to_dict())
        print("numeric describe:")
        print(full.describe(include='all').to_string())
    except Exception as e:
        print("describe error", e)