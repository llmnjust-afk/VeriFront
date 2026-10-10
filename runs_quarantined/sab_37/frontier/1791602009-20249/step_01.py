import os
import json
import pandas as pd

path = "mist_hr/hr_sample_mist.xlsx"
print("Exists:", os.path.exists(path), "Size:", os.path.getsize(path) if os.path.exists(path) else None)

# Inspect workbook sheets and columns/shapes
xl = pd.ExcelFile(path)
print("Sheets:", xl.sheet_names)

for sheet in xl.sheet_names:
    try:
        df_head = pd.read_excel(path, sheet_name=sheet, nrows=10)
        df_full = pd.read_excel(path, sheet_name=sheet)
        print("\nSHEET", repr(sheet))
        print("shape:", df_full.shape)
        print("columns:", list(df_full.columns))
        print("head:")
        print(df_head.to_string(index=False))
        print("dtypes:")
        print(df_full.dtypes.to_string())
        print("describe numeric:")
        print(df_full.describe().to_string())
    except Exception as e:
        print("Error reading sheet", sheet, e)