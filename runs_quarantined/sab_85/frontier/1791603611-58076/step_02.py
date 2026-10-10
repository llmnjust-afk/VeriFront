import os
from pathlib import Path

print("Current working directory:", os.getcwd())
print("Top-level directory listing:")
for p in sorted(Path(".").iterdir()):
    print(("DIR " if p.is_dir() else "FILE"), p)

print("\nSearching for data.pkl and saliva_data directories under current tree (limited):")
matches = []
for root, dirs, files in os.walk("."):
    # prune hidden/cache-ish large dirs lightly
    parts = Path(root).parts
    if any(part in {".git", "__pycache__", ".pytest_cache"} for part in parts):
        continue
    if "data.pkl" in files or Path(root).name == "saliva_data":
        matches.append(root)
        print("MATCH DIR:", root, "files:", files[:10])
    if len(matches) > 50:
        print("Stopping search after 50 matches")
        break

print("\nParent directory listing:")
parent = Path("..")
for p in sorted(parent.iterdir())[:100]:
    print(("DIR " if p.is_dir() else "FILE"), p)