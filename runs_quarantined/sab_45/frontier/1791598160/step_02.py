#!/usr/bin/env python3
from pathlib import Path
import os

def main():
    print(f"Current working directory: {Path.cwd()}")
    print("Top-level entries in current directory:")
    for p in sorted(Path(".").iterdir()):
        print(("DIR " if p.is_dir() else "FILE") + str(p))
    print("\nSearching for questionnaire_data.pkl under current directory and common parents...")
    search_roots = [Path("."), Path(".."), Path("../.."), Path("/data/lab/VeriFront")]
    found = []
    for root in search_roots:
        if root.exists():
            try:
                for p in root.rglob("questionnaire_data.pkl"):
                    found.append(p)
                    print(f"FOUND: {p.resolve()}")
            except PermissionError as e:
                print(f"PermissionError searching {root}: {e}")
    if not found:
        print("No questionnaire_data.pkl found in searched locations.")
    else:
        print(f"Total found: {len(found)}")

if __name__ == "__main__":
    main()