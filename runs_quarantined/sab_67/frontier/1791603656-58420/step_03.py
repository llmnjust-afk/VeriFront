from pathlib import Path
import os
import numpy as np
import pandas as pd

cwd = Path.cwd()
print("CWD:", cwd)

print("\nRecursive listing of benchmark and pred_results (limited):")
for root_name in ["benchmark", "pred_results"]:
    root = cwd / root_name
    print("\nROOT", root, "exists", root.exists())
    if root.exists():
        count = 0
        for dirpath, dirnames, filenames in os.walk(root):
            depth = len(Path(dirpath).relative_to(root).parts)
            indent = "  " * depth
            print(f"{indent}{Path(dirpath).name}/")
            for fn in sorted(filenames)[:20]:
                p = Path(dirpath) / fn
                print(f"{indent}  {fn} ({p.stat().st_size} bytes)")
            count += 1
            if count > 200:
                print("... truncated")
                break

print("\nFinding all csv/npy files under current working directory:")
all_files = []
for ext in ["*.csv", "*.npy", "*.npz", "*.pkl", "*.json", "*.txt", "*.py"]:
    all_files.extend(cwd.rglob(ext))
for p in sorted(all_files):
    print(p.relative_to(cwd), p.stat().st_size)

# inspect likely benchmark files
print("\nPython files preview:")
for p in sorted((cwd/"benchmark").rglob("*.py"))[:20]:
    print("\n---", p.relative_to(cwd), "---")
    try:
        txt = p.read_text(errors="replace")
        print(txt[:4000])
    except Exception as e:
        print("ERROR", e)