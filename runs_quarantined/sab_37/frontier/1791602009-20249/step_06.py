from pathlib import Path
import inspect
import pandas as pd
import numpy as np

from biopsykit.protocols.cft import CFT

print("CFT class source:")
src = inspect.getsource(CFT)
print(src)

print("\nCFT methods/signatures:")
for name, obj in inspect.getmembers(CFT):
    if not name.startswith("_") and (inspect.isfunction(obj) or isinstance(obj, property)):
        print(name, type(obj))
        if inspect.isfunction(obj):
            try:
                print(" ", inspect.signature(obj))
            except Exception as e:
                print(" sig err", e)
            doc = inspect.getdoc(obj)
            if doc:
                print(" doc", doc[:500].replace("\n", " | "))

# Attempt typical construction and inspect attributes
path = Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx")
df = pd.read_excel(path, sheet_name="MIST3")
print("\nData index/columns variants:")
print(df.head().to_string(index=False))
hr1 = df.set_index("time")
print("hr1 head")
print(hr1.head())

try:
    cft = CFT()
    print("CFT instance dict:", cft.__dict__)
    print("default structure:", getattr(cft, "structure", None))
except Exception as e:
    print("CFT init failed:", repr(e))