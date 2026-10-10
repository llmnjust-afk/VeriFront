#!/usr/bin/env python3
import os
import json
from pathlib import Path

print("Current working directory:", os.getcwd())
print("\nTop-level directory listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "DIR" if p.is_dir() else "FILE")

print("\nSearching for data.pkl and saliva-like paths...")
matches = []
for root, dirs, files in os.walk("."):
    # skip hidden-ish/cache large dirs conservatively
    parts = Path(root).parts
    if any(part in {".git", "__pycache__", ".ipynb_checkpoints"} for part in parts):
        continue
    for name in files:
        if name == "data.pkl" or "saliva" in str(Path(root) / name).lower():
            matches.append(str(Path(root) / name))
    for d in dirs:
        if "saliva" in d.lower():
            matches.append(str(Path(root) / d) + "/")
for m in sorted(matches)[:200]:
    print(" ", m)
print(f"Found {len(matches)} matching paths")

# If no local data exists, create an explanatory marker but do not fabricate final output.
os.makedirs("pred_results", exist_ok=True)
with open("pred_results/_search_log.json", "w", encoding="utf-8") as f:
    json.dump({"cwd": os.getcwd(), "matches": sorted(matches)}, f, indent=2)
print("\nWrote search log to pred_results/_search_log.json")