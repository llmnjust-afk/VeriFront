#!/usr/bin/env python3
import os
import glob
from pathlib import Path

print("Current working directory:", os.getcwd())
print("Top-level entries:")
for p in sorted(Path(".").iterdir()):
    print(" -", p, "dir" if p.is_dir() else "file")

print("\nSearching for questionnaire_data.pkl under current tree (limited display):")
matches = list(Path(".").rglob("questionnaire_data.pkl"))
for m in matches[:50]:
    print("FOUND", m)
print("Total matches:", len(matches))

print("\nSearching one level up if accessible:")
try:
    matches_up = list(Path("..").rglob("questionnaire_data.pkl"))
    for m in matches_up[:50]:
        print("FOUND_UP", m)
    print("Total matches up:", len(matches_up))
except Exception as e:
    print("Search up failed:", repr(e))

print("\nDirectory tree sample:")
count = 0
for root, dirs, files in os.walk("."):
    level = root.count(os.sep)
    if level > 3:
        dirs[:] = []
        continue
    indent = "  " * level
    print(f"{indent}{os.path.basename(root) or '.'}/")
    for f in files[:10]:
        print(f"{indent}  {f}")
    count += 1
    if count > 80:
        print("... truncated")
        break