import os
from pathlib import Path

search_roots = [Path.cwd(), Path.cwd().parent, Path("/data/lab/VeriFront"), Path("/data/lab")]
seen = set()
for sr in search_roots:
    if not sr.exists() or sr in seen:
        continue
    seen.add(sr)
    print(f"\nSearching under {sr} (limited)...")
    count = 0
    for root, dirs, files in os.walk(sr):
        # prune very large/unrelated dirs conservatively
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules")]
        for name in files:
            low = name.lower()
            if "hr_sample_mist" in low or (("mist" in low or "cft" in low or "heart" in low) and low.endswith((".xlsx",".xls",".csv",".json",".parquet"))):
                p = Path(root) / name
                print("FOUND", p, p.stat().st_size)
                count += 1
                if count >= 50:
                    break
        if count >= 50:
            print("Stopping after 50 matches")
            break
    print("matches:", count)