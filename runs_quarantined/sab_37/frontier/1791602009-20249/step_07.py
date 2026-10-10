import inspect
from pathlib import Path
import pandas as pd
from biopsykit.protocols.cft import CFT

# Print only the methods relevant to the required outputs
for name in ["compute_cft_parameter", "baseline_hr", "onset"]:
    obj = getattr(CFT, name)
    print("\n" + "="*80)
    print("METHOD", name, "signature", inspect.signature(obj))
    print(inspect.getsource(obj))

# Try running BioPsyKit CFT parameter computation on MIST3 with default structure.
path = Path("benchmark/datasets/mist_hr/hr_sample_mist.xlsx")
if not path.exists():
    path = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/mist_hr/hr_sample_mist.xlsx")
df = pd.read_excel(path, sheet_name="MIST3")
data = df.set_index("time")
print("\nInput data:")
print(data.head().to_string())
print(data.index.dtype, data.shape)

for structure in [None, {"Baseline": 60, "CFT": 120, "Recovery": 60}]:
    try:
        cft = CFT(structure=structure)
        res_df = cft.compute_cft_parameter(data)
        res_dict = cft.compute_cft_parameter(data, return_dict=True)
        print("\nStructure:", cft.structure, "cft_start:", cft.cft_start, "cft_duration:", cft.cft_duration)
        print("Result DataFrame:")
        print(res_df.to_string())
        print("Result dict:")
        print(res_dict)
    except Exception as e:
        print("\nCFT computation failed for structure", structure, ":", repr(e))