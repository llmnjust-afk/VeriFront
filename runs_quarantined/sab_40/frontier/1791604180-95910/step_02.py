#!/usr/bin/env python3
import os
from pathlib import Path

print("cwd:", os.getcwd())
print("top-level listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else "file", p.stat().st_size if p.is_file() else "")

print("\nSearching for dataset files under cwd (max depth unconstrained):")
targets = {"mol_descriptors_training.csv", "standardized_compounds_excl_ambiguous_cluster.csv", "test.csv"}
found = []
for root, dirs, files in os.walk("."):
    # avoid huge hidden/system dirs
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"__pycache__", "pred_results"}]
    for f in files:
        if f in targets or "dili" in f.lower() or "descriptor" in f.lower():
            path = os.path.join(root, f)
            found.append(path)
            print(path, os.path.getsize(path))
print("found count:", len(found))

print("\nSearching one level up if accessible:")
parent = Path("..").resolve()
print("parent:", parent)
try:
    for p in sorted(parent.iterdir())[:100]:
        print(" ", p.name, "dir" if p.is_dir() else "file")
except Exception as e:
    print("parent list failed:", repr(e))