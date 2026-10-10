#!/usr/bin/env python3
import os
from pathlib import Path
import json
import fnmatch

roots = [Path("."), Path("benchmark/datasets"), Path("/data/lab/VeriFront/runs/sab_85")]
patterns = ["*saliva*", "*Saliva*", "data.pkl"]
found = []

for base in roots:
    if not base.exists():
        continue
    print(f"Searching {base} ...")
    n_dirs = 0
    for root, dirs, files in os.walk(base):
        n_dirs += 1
        # prune very large/generated output dirs and already-searched step artifacts
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "pred_results"}]
        rp = Path(root)
        for d in dirs:
            rel = rp / d
            if any(fnmatch.fnmatch(d, pat) or fnmatch.fnmatch(str(rel), pat) for pat in patterns):
                found.append(("dir", str(rel)))
        for f in files:
            rel = rp / f
            if any(fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(str(rel), pat) for pat in patterns):
                found.append(("file", str(rel)))
        if n_dirs % 1000 == 0:
            print(f"  visited {n_dirs} dirs, found {len(found)}")
        if n_dirs > 20000 and base == Path("/data/lab/VeriFront/runs/sab_85"):
            print("  stopping wide search after 20000 dirs")
            break
    print(f"Finished {base}: visited {n_dirs} dirs")

# Deduplicate preserving order
seen = set()
unique = []
for typ, path in found:
    key = (typ, path)
    if key not in seen:
        seen.add(key)
        unique.append({"type": typ, "path": path})

print("\nMatches:")
for item in unique[:300]:
    print(f"  {item['type']}: {item['path']}")
print("Total unique matches:", len(unique))

os.makedirs("pred_results", exist_ok=True)
with open("pred_results/_focused_search_log.json", "w", encoding="utf-8") as fh:
    json.dump(unique, fh, indent=2)
print("Saved pred_results/_focused_search_log.json")