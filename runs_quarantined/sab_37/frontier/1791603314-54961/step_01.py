import os
import json
import pandas as pd

path = "mist_hr/hr_sample_mist.xlsx"
print("Exists:", os.path.exists(path), "size:", os.path.getsize(path) if os.path.exists(path) else None)

xl = pd.ExcelFile(path)
print("Sheets:", xl.sheet_names)

for sheet in xl.sheet_names:
    try:
        df_head = pd.read_excel(path, sheet_name=sheet, nrows=10)
        print("\nSHEET", repr(sheet))
        print("shape first rows:", df_head.shape)
        print("columns:", list(df_head.columns))
        print(df_head.head(5).to_string(index=False))
    except Exception as e:
        print("Error reading", sheet, e)