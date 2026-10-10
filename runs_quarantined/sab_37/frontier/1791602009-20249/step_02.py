import os
from pathlib import Path

print("CWD:", os.getcwd())
print("Top-level directory listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size}")

print("\nSearching for Excel/CSV/data-like files under current tree (limited):")
matches = []
for root, dirs, files in os.walk("."):
    # skip hidden/cache maybe
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"__pycache__"}]
    for f in files:
        if f.lower().endswith((".xlsx", ".xls", ".csv", ".tsv", ".txt", ".json")):
            full = Path(root) / f
            matches.append(full)
for p in sorted(matches)[:200]:
    print(" ", p, p.stat().st_size)
print("Total matches:", len(matches))

print("\nSearching nearby /data paths for hr_sample_mist.xlsx (limited):")
for base in [Path("/data"), Path("/mnt/data"), Path("/tmp")]:
    if base.exists():
        count = 0
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"__pycache__"}]
            if "hr_sample_mist.xlsx" in files or "mist_hr" in root:
                print("root:", root, "files:", files[:10])
            count += 1
            if count > 5000:
                print("stopped scanning", base, "after", count, "dirs")
                break