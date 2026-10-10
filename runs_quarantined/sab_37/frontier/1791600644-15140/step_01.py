import os
import json
from pathlib import Path

import pandas as pd

xlsx_path = Path("mist_hr/hr_sample_mist.xlsx")
print(f"Exists: {xlsx_path.exists()}, size={xlsx_path.stat().st_size if xlsx_path.exists() else 'NA'}")

xl = pd.ExcelFile(xlsx_path)
print("Sheets:", xl.sheet_names)

for sheet in xl.sheet_names:
    try:
        df_head = pd.read_excel(xlsx_path, sheet_name=sheet, nrows=8)
        print("\n--- Sheet:", sheet, "---")
        print("shape(head):", df_head.shape)
        print("columns:", list(df_head.columns))
        print(df_head.head().to_string(index=False))
    except Exception as e:
        print("Error reading", sheet, repr(e))