import os
from pathlib import Path

print("CWD:", os.getcwd())
print("Top-level entries:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size}")

print("\nSearching for Excel files and mist-related paths...")
for root, dirs, files in os.walk("."):
    # limit noisy hidden/cache dirs
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__",)]
    for name in files:
        low = name.lower()
        if low.endswith((".xlsx", ".xls", ".csv", ".json")) or "mist" in low or "hr" in low:
            p = Path(root) / name
            print(p, p.stat().st_size)