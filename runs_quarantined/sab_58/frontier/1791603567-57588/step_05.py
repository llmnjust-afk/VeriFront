#!/usr/bin/env python3
import os, glob
base="benchmark/datasets/nvc"
print("Python/scripts under nvc:")
for path in sorted(glob.glob(base+"/**/*.py", recursive=True)):
    print("\n###", path)
    with open(path, encoding="utf-8") as f:
        content=f.read()
    print(content[:4000])
    if len(content)>4000:
        print(f"\n... truncated, total chars {len(content)}")
print("\nCSV list under nvc/scripts:")
for path in sorted(glob.glob(base+"/scripts/**/*.csv", recursive=True)):
    print(path)