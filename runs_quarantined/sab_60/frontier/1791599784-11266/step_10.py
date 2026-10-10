#!/usr/bin/env python3
from pathlib import Path
for name in ["particularity.py","partneg.py"]:
    p=Path("benchmark/datasets/nvc/scripts/nvc_prediction/rules")/name
    print(f"\n===== {name} =====")
    for i,line in enumerate(p.read_text().splitlines(),1):
        print(f"{i:03d}: {line}")