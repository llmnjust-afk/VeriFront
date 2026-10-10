#!/usr/bin/env python3
from pathlib import Path
root=Path("benchmark/datasets/nvc/scripts/nvc_prediction/rules")
for name in ["atmosphere.py","emptystart.py","figural.py","negativity.py","particularity.py","partneg.py"]:
    p=root/name
    print(f"\n===== {name} =====")
    print(p.read_text())