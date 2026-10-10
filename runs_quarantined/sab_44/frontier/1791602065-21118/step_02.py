#!/usr/bin/env python3
import os
from pathlib import Path
import importlib, inspect

print("CWD:", os.getcwd())
print("Top-level listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size}")

print("\nSearching for sleep_data.pkl (limited)...")
matches = []
for root, dirs, files in os.walk("."):
    # skip hidden/cache large irrelevant
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache", "node_modules"}]
    if "sleep_data.pkl" in files:
        matches.append(Path(root)/"sleep_data.pkl")
for m in matches:
    print("FOUND", m, "size", m.stat().st_size)
print("Total matches:", len(matches))

print("\nInspecting biopsykit sleep modules...")
try:
    import biopsykit
    print("biopsykit version:", getattr(biopsykit, "__version__", "unknown"))
    print("biopsykit path:", biopsykit.__file__)
    # List modules containing sleep
    import pkgutil
    sleep_mods = []
    for mod in pkgutil.walk_packages(biopsykit.__path__, biopsykit.__name__ + "."):
        if "sleep" in mod.name.lower():
            sleep_mods.append(mod.name)
    for name in sleep_mods[:100]:
        print(" module:", name)
    print("sleep module count:", len(sleep_mods))
except Exception as e:
    print("Error inspecting biopsykit:", repr(e))