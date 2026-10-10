#!/usr/bin/env python3
import os
from pathlib import Path
import json

print("CWD:", os.getcwd())
print("\nRecursive listing of benchmark (limited):")
count = 0
for root, dirs, files in os.walk("benchmark"):
    level = len(Path(root).parts) - len(Path("benchmark").parts)
    indent = "  " * level
    print(f"{indent}{Path(root).name}/")
    for fn in sorted(files)[:50]:
        fp = Path(root) / fn
        try:
            size = fp.stat().st_size
        except OSError:
            size = None
        print(f"{indent}  {fn} ({size} bytes)")
        count += 1
    if count > 500:
        print("... stopping after 500 files")
        break

print("\nSearching wider under /data/lab/VeriFront/runs/sab_85 for saliva_data/data.pkl ...")
matches = []
base = Path("/data/lab/VeriFront/runs/sab_85")
if base.exists():
    for root, dirs, files in os.walk(base):
        # prune obviously irrelevant generated dirs? keep modest
        if "data.pkl" in files:
            fp = Path(root) / "data.pkl"
            if "saliva" in str(fp).lower() or True:
                matches.append(str(fp))
        # avoid too much output; don't prune yet
        if len(matches) > 100:
            break
for m in matches[:100]:
    print(" ", m)
print("Total data.pkl matches:", len(matches))

with open("pred_results/_wide_search_log.json", "w", encoding="utf-8") as f:
    json.dump({"matches": matches[:500]}, f, indent=2)
print("Saved wide search log.")