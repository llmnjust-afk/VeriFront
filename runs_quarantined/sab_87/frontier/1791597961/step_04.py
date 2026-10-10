#!/usr/bin/env python3
from pathlib import Path
import os

# Focused search for climate/polynomial files in accessible likely locations.
roots = [Path("."), Path("/data"), Path("/mnt"), Path("/tmp")]
patterns = ["*.nc", "*north*america*", "*A1B*", "*polynomial*"]
seen = set()
for root in roots:
    if not root.exists():
        continue
    print(f"\nSearching under {root} ...")
    n = 0
    try:
        for pat in patterns:
            for p in root.rglob(pat):
                sp = str(p.resolve()) if p.exists() else str(p)
                if sp in seen:
                    continue
                seen.add(sp)
                try:
                    kind = "dir" if p.is_dir() else f"file {p.stat().st_size} bytes"
                except Exception as e:
                    kind = f"? {e}"
                print(" ", p, kind)
                n += 1
                if n >= 100:
                    print("  ...limit reached")
                    raise StopIteration
    except StopIteration:
        pass
    except Exception as e:
        print(" search error:", type(e).__name__, e)

print("\nPred results current:")
pr = Path("pred_results")
pr.mkdir(exist_ok=True)
for p in sorted(pr.iterdir()):
    print(p, p.stat().st_size if p.is_file() else "dir")