#!/usr/bin/env python3
from pathlib import Path
import os
import shutil

print("Explicit search for polynomial_fit/A1B_north_america.nc and related names...")
roots = [Path("benchmark"), Path("/data/lab/VeriFront")]
patterns = ["A1B_north_america.nc", "polynomial_fit", "north_america", "A1B"]
found = []

for base in roots:
    if not base.exists():
        continue
    print(f"Searching under {base} ...")
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".cache", "node_modules"}]
        rpath = Path(root)
        for d in dirs:
            if any(p.lower() in d.lower() for p in patterns):
                found.append(("dir", str(rpath/d), None))
        for f in files:
            if any(p.lower() in f.lower() for p in patterns) or f.lower().endswith(".nc"):
                p = rpath/f
                try:
                    size = p.stat().st_size
                except Exception:
                    size = None
                found.append(("file", str(p), size))
        if len(found) > 300:
            break
    print(f"  cumulative found: {len(found)}")
    if len(found) > 300:
        break

print("Matches:")
for kind, p, size in found[:300]:
    print(kind, p, "" if size is None else f"size={size}")
print(f"Total matches listed: {min(len(found),300)} of {len(found)}")

# If exact file found elsewhere, copy/symlink to expected relative location for later use
exact = [Path(p) for kind, p, size in found if kind == "file" and Path(p).name == "A1B_north_america.nc"]
print(f"Exact A1B_north_america.nc files: {exact}")
if exact:
    dest = Path("polynomial_fit/A1B_north_america.nc")
    dest.parent.mkdir(exist_ok=True)
    if not dest.exists():
        shutil.copy2(exact[0], dest)
        print(f"Copied {exact[0]} -> {dest}")
    print(f"Ready dataset at {dest}, size={dest.stat().st_size}")