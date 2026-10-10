#!/usr/bin/env python3
from pathlib import Path
import os

def main():
    print("CWD:", Path.cwd())
    b = Path("benchmark")
    print("benchmark exists:", b.exists(), "is_dir:", b.is_dir(), "is_symlink:", b.is_symlink())
    if b.exists():
        print("benchmark resolved:", b.resolve())
        print("benchmark entries (first 200):")
        try:
            for i, p in enumerate(sorted(b.iterdir())):
                if i >= 200:
                    print("  ...")
                    break
                print(" ", p, "dir" if p.is_dir() else "file", "symlink" if p.is_symlink() else "")
        except Exception as e:
            print("Error listing benchmark:", repr(e))

    print("\nSearching with followlinks=True for jnmf_visualization and .npy...")
    found_dirs = []
    found_files = []
    for root, dirs, files in os.walk(".", followlinks=True):
        rp = Path(root)
        if rp.name == "jnmf_visualization":
            found_dirs.append(rp)
        for f in files:
            if f.endswith(".npy") or "jnmf" in f.lower() or "conscientiousness" in f.lower():
                found_files.append(rp / f)
        if len(found_files) > 500:
            break

    print("Found dirs:")
    for d in found_dirs[:50]:
        print(" ", d)
        try:
            for p in sorted(d.iterdir()):
                print("    ", p.name)
        except Exception as e:
            print("    list error", repr(e))
    print("Found candidate files:")
    for f in found_files[:200]:
        print(" ", f)

if __name__ == "__main__":
    main()