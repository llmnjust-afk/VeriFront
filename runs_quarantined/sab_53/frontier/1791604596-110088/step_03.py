#!/usr/bin/env python3
"""
Inspect the available benchmark directory to locate the input rasters or any
pre-existing reclassified rasters that can be standardized/copied to the required
pred_results outputs.
"""
from pathlib import Path
import os
import sys

print("Current working directory:", Path.cwd())

roots = [Path("."), Path("benchmark"), Path("/data/lab/VeriFront")]
patterns = ["*.tif", "*.tiff", "*.tfw", "*.geojson", "*.dbf", "*.xml"]

for root in roots:
    if not root.exists():
        print(f"\nRoot missing: {root}")
        continue
    print(f"\n=== Inspecting {root.resolve()} ===")
    count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            # Avoid massive traversal outside this run; cap printed files.
            rel_dir = Path(dirpath)
            interesting = []
            for fn in filenames:
                low = fn.lower()
                if any(low.endswith(pat.replace("*", "")) for pat in patterns) or "land" in low or "protect" in low:
                    interesting.append(fn)
            if interesting:
                print(f"\nDirectory: {rel_dir}")
                for fn in sorted(interesting):
                    p = rel_dir / fn
                    try:
                        size = p.stat().st_size
                    except Exception:
                        size = "?"
                    print(f"  {fn}  size={size}")
                    count += 1
                    if count >= 300:
                        print("  ... print cap reached ...")
                        raise StopIteration
    except StopIteration:
        pass
    except Exception as e:
        print(f"Error walking {root}: {e!r}")

print("\nDirect benchmark tree:")
if Path("benchmark").exists():
    for p in sorted(Path("benchmark").rglob("*"))[:500]:
        typ = "DIR " if p.is_dir() else "FILE"
        try:
            size = "" if p.is_dir() else f" size={p.stat().st_size}"
        except Exception:
            size = ""
        print(f" {typ} {p}{size}")

print("\nDone inspection.")