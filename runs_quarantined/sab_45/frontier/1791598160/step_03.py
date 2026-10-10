#!/usr/bin/env python3
from pathlib import Path
import os

def list_dir(path, max_entries=200):
    print(f"\nListing {path}:")
    try:
        entries = sorted(Path(path).iterdir())
        for i, p in enumerate(entries[:max_entries]):
            print(f"{i:03d} {'DIR ' if p.is_dir() else 'FILE'} {p}")
        if len(entries) > max_entries:
            print(f"... {len(entries) - max_entries} more entries")
    except Exception as e:
        print(f"Could not list {path}: {type(e).__name__}: {e}")

def main():
    print(f"CWD: {Path.cwd()}")
    for path in [".", "benchmark", "benchmark/biopsykit_questionnaire_data", "/data/lab/VeriFront/runs/sab_45/frontier/1791598160/benchmark"]:
        list_dir(path)
    print("\nSearching inside benchmark for pickle/csv/parquet/data files:")
    root = Path("benchmark")
    if root.exists():
        for p in sorted(root.rglob("*")):
            if p.is_file() and (p.suffix.lower() in [".pkl", ".pickle", ".csv", ".parquet", ".feather", ".json"] or "questionnaire" in p.name.lower()):
                print(p, p.stat().st_size)

if __name__ == "__main__":
    main()