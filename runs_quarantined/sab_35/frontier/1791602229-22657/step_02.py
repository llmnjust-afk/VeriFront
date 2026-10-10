#!/usr/bin/env python3
import os
import glob

print("Working directory:", os.getcwd())
print("Top-level listing:")
for p in sorted(os.listdir(".")):
    print(" ", p)

print("\nSearching for bio_eventrelated_100hz.csv under common roots...")
roots = [".", "/data", "/mnt", "/tmp"]
matches = []
for root in roots:
    try:
        found = glob.glob(os.path.join(root, "**", "bio_eventrelated_100hz.csv"), recursive=True)
        matches.extend(found)
        print(f"{root}: {len(found)} matches")
        for f in found[:10]:
            print(" ", f)
    except Exception as e:
        print(f"{root}: error {e!r}")

print("\nAll matches:")
for f in matches:
    print(f)

# Also list parent directories containing biosignals if any
print("\nSearching for biosignals directories...")
bios = []
for root in roots:
    try:
        found = [p for p in glob.glob(os.path.join(root, "**", "biosignals"), recursive=True) if os.path.isdir(p)]
        bios.extend(found)
        print(f"{root}: {len(found)} biosignals dirs")
        for b in found[:10]:
            print(" ", b, "contains:", os.listdir(b)[:10])
    except Exception as e:
        print(f"{root}: error {e!r}")