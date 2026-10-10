import os
from pathlib import Path

roots = [Path("."), Path("/data/lab/VeriFront/runs"), Path("/data/lab/VeriFront"), Path("/tmp"), Path("/mnt/data")]
patterns = ["hr_sample_mist", "mist_hr", "MIST3", "mist"]
found = []

for base in roots:
    if not base.exists():
        continue
    print(f"Searching under {base} ...")
    visited = 0
    for root, dirs, files in os.walk(base):
        visited += 1
        # prune hidden/cache-ish and very deep trees
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "node_modules"}]
        if visited > 20000:
            print("  stopping after 20000 dirs")
            break
        for d in list(dirs):
            if any(p.lower() in d.lower() for p in patterns):
                path = Path(root) / d
                found.append(path)
                print("  FOUND DIR", path)
        for f in files:
            low = f.lower()
            if any(p.lower() in low for p in patterns) or low.endswith(".xlsx"):
                path = Path(root) / f
                try:
                    size = path.stat().st_size
                except Exception:
                    size = "?"
                found.append(path)
                print("  FOUND FILE", path, "size", size)
    print("  visited", visited, "dirs")

print("\nSummary found count:", len(found))
for p in found[:200]:
    print(p)