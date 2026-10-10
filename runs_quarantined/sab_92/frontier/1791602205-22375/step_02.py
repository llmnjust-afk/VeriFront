#!/usr/bin/env python3
from pathlib import Path
import os

def main():
    print("Current working directory:", Path.cwd())
    print("Top-level entries:")
    for p in sorted(Path(".").iterdir()):
        print(" ", p, "dir" if p.is_dir() else "file")
    print("\nSearching for jnmf_visualization directories and relevant .npy files...")
    matches = []
    for root, dirs, files in os.walk("."):
        root_path = Path(root)
        if root_path.name == "jnmf_visualization":
            print("Found directory:", root_path)
            for f in sorted(files):
                print("  ", f)
        for f in files:
            if "conscientiousness" in f and f.endswith(".npy"):
                matches.append(root_path / f)
    print("\nMatched npy files:")
    for m in sorted(matches):
        print(" ", m)

if __name__ == "__main__":
    main()