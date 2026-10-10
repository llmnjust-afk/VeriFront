#!/usr/bin/env python3
import os
from pathlib import Path
import json

print("Working directory:", os.getcwd())
print("Listing .:", os.listdir("."))

# Thoroughly inspect benchmark and nearby structure; previous search found no filenames containing dkpes.
for target in [".", "benchmark", "/data/lab/VeriFront/runs/sab_5/frontier/1791604640-110427/benchmark"]:
    p = Path(target)
    print(f"\n=== {target} ===")
    print("exists:", p.exists(), "is_dir:", p.is_dir(), "is_symlink:", p.is_symlink())
    if p.exists():
        try:
            print("resolve:", p.resolve())
        except Exception as e:
            print("resolve error:", repr(e))
        try:
            print("listdir:", os.listdir(p)[:100])
        except Exception as e:
            print("listdir error:", repr(e))

print("\nRecursive file listing under current directory:")
all_files = []
for root, dirs, files in os.walk(".", followlinks=True):
    print("ROOT", root, "DIRS", dirs, "FILES", files[:20])
    for fn in files:
        all_files.append(os.path.join(root, fn))
print("\nTotal files found:", len(all_files))
for f in all_files[:200]:
    print(f)

# Search wider likely mount roots, limited output
print("\nSearching likely roots for dkpes_train.csv/dkpes_test.csv (limited)...")
search_roots = ["/data/lab/VeriFront", "/data/lab", "/data", "/tmp"]
found = []
for sr in search_roots:
    if not os.path.exists(sr):
        continue
    print("search root:", sr)
    count_dirs = 0
    try:
        for root, dirs, files in os.walk(sr, followlinks=True):
            count_dirs += 1
            if count_dirs % 5000 == 0:
                print("  visited dirs", count_dirs, "currently", root)
            for fn in files:
                low = fn.lower()
                if low in ("dkpes_train.csv", "dkpes_test.csv") or "dkpes" in low:
                    path = os.path.join(root, fn)
                    found.append(path)
                    print("FOUND", path)
            if len(found) >= 20:
                break
    except Exception as e:
        print("walk error for", sr, repr(e))
    print("visited", count_dirs, "dirs in", sr)
    if found:
        break

with open("file_search_results.json", "w") as f:
    json.dump({"found": found, "all_files_here": all_files}, f, indent=2)
print("\nFound paths:", found)
print("Wrote file_search_results.json")
if not found:
    raise SystemExit("No DKPES files found in searched locations.")