import os
from pathlib import Path

print("CWD:", os.getcwd())
print("Top-level directory listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else f"file size={p.stat().st_size}")

print("\nSearching for Excel/CSV/data-like files up to depth 5:")
matches = []
for root, dirs, files in os.walk("."):
    depth = Path(root).parts
    if len(depth) > 6:
        dirs[:] = []
        continue
    for f in files:
        if f.lower().endswith((".xlsx", ".xls", ".csv", ".tsv", ".txt", ".json")):
            path = Path(root) / f
            matches.append(path)
            print(" ", path, "size", path.stat().st_size)
print("Total matches:", len(matches))