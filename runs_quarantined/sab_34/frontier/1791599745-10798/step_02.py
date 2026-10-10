#!/usr/bin/env python3
import os
from pathlib import Path
import glob

print("CWD:", os.getcwd())
print("Top-level entries:")
for p in sorted(Path(".").iterdir()):
    print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size} bytes")

patterns = [
    "biosignals/bio_resting_5min_100hz.csv",
    "../**/bio_resting_5min_100hz.csv",
    "/data/lab/**/bio_resting_5min_100hz.csv",
    "/mnt/data/**/bio_resting_5min_100hz.csv",
    "/tmp/**/bio_resting_5min_100hz.csv",
]
found = []
for pat in patterns:
    print("Searching pattern:", pat)
    try:
        matches = glob.glob(pat, recursive=True)
    except Exception as e:
        print("  error:", repr(e))
        matches = []
    print("  matches:", len(matches))
    for m in matches[:20]:
        print("   ", m)
    found.extend(matches)

# If found, create local expected symlink/copy-friendly path record and summarize first match.
if found:
    src = Path(found[0])
    print("Using first found:", src, "exists:", src.exists(), "size:", src.stat().st_size)
    import pandas as pd
    df = pd.read_csv(src)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print(df.head().to_string())
    print(df.describe().to_string())
    Path("biosignals").mkdir(exist_ok=True)
    target = Path("biosignals/bio_resting_5min_100hz.csv")
    if not target.exists():
        try:
            target.symlink_to(src.resolve())
            print("Created symlink:", target, "->", src.resolve())
        except Exception as e:
            print("Symlink failed:", repr(e))
            import shutil
            shutil.copy2(src, target)
            print("Copied to:", target)
else:
    print("No dataset found in searched locations.")