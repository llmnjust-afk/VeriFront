import os
from pathlib import Path
import pandas as pd
import numpy as np

cwd = Path.cwd()
print("Working directory:", cwd)
print("Top-level working dir contents:")
for p in sorted(cwd.iterdir()):
    print(" -", p.name, "dir" if p.is_dir() else f"{p.stat().st_size} bytes")

print("\nSearching for dataset files nearby...")
targets = ["Atmosphere.csv", "fit_result_openness_W_high.npy", "CogSci_pattern_high_sim_data"]
search_roots = [cwd, cwd.parent, Path("/data/lab/VeriFront/runs"), Path("/data/lab/VeriFront")]
found = []
seen = set()
for root in search_roots:
    if not root.exists() or root in seen:
        continue
    seen.add(root)
    print("Searching root:", root)
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            # prune hidden/cache-ish and too deep relative to root
            rel = Path(dirpath).relative_to(root)
            if len(rel.parts) > 6:
                dirnames[:] = []
                continue
            names = set(filenames) | set(dirnames)
            if any(t in names for t in targets) or Path(dirpath).name == "CogSci_pattern_high_sim_data":
                found.append(Path(dirpath))
                print(" FOUND candidate:", dirpath, "files:", filenames[:10], "dirs:", dirnames[:10])
    except Exception as e:
        print(" Search error for", root, ":", repr(e))

print("\nCandidates:", len(found))
for f in found[:20]:
    print(f)

# If found, inspect first directory that contains the expected csv/npy files
base = None
for cand in found:
    if cand.name == "CogSci_pattern_high_sim_data":
        base = cand
        break
    sub = cand / "CogSci_pattern_high_sim_data"
    if sub.exists():
        base = sub
        break
    if (cand / "Atmosphere.csv").exists():
        base = cand
        break

print("\nSelected base:", base)
if base is not None and base.exists():
    print("Selected files:")
    for p in sorted(base.iterdir()):
        print(" -", p.name, p.stat().st_size, "bytes")
    for npy in sorted(base.glob("*.npy")):
        arr = np.load(npy, allow_pickle=True)
        print("\nNPY:", npy.name, "dtype:", arr.dtype, "shape:", arr.shape, "ndim:", arr.ndim)
        if arr.dtype == object:
            for i, x in enumerate(arr.ravel()[:5]):
                print(" item", i, type(x), repr(x)[:500])
        else:
            print(" min/max/sum:", float(np.nanmin(arr)), float(np.nanmax(arr)), float(np.nansum(arr)))
            print(" first:", arr.ravel()[:20])
    for csv in sorted(base.glob("*.csv")):
        df = pd.read_csv(csv)
        print("\nCSV:", csv.name, "shape:", df.shape)
        print(df.head().to_string(index=False))
else:
    print("No dataset base found.")