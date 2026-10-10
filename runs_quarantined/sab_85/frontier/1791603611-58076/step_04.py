import os
from pathlib import Path

candidate_roots = [
    Path("saliva_data"),
    Path("benchmark/datasets/saliva_data"),
    Path("benchmark/datasets/saliva"),
    Path("benchmark/saliva_data"),
    Path("/data/lab/VeriFront/runs/sab_85/frontier/1791602474-24226/saliva_data"),
    Path("/data/lab/VeriFront/runs/sab_85/frontier/1791602474-24226/benchmark/datasets/saliva_data"),
]
print("Candidate paths:")
for p in candidate_roots:
    print(p, "exists=", p.exists(), "is_dir=", p.is_dir())
    if p.exists() and p.is_dir():
        print("  files:", list(p.iterdir())[:20])

print("\nUsing pathlib glob for *saliva* and data.pkl under benchmark/datasets:")
for pattern in ["benchmark/datasets/**/data.pkl", "benchmark/datasets/**/*saliva*", "**/data.pkl", "**/*saliva*"]:
    print(f"\nPattern: {pattern}")
    found = 0
    for p in Path(".").glob(pattern):
        print(" ", p, "dir" if p.is_dir() else f"file {p.stat().st_size} bytes")
        found += 1
        if found >= 30:
            print("  ... stopping at 30")
            break
    print(" found count shown:", found)