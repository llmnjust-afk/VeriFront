#!/usr/bin/env python3
from pathlib import Path
import json

print("Inspecting benchmark directory and any hints for expected output format...")
bench = Path("benchmark")
if bench.exists():
    for p in sorted(bench.rglob("*")):
        if p.is_file():
            print(f"\n--- FILE {p} size={p.stat().st_size} ---")
            try:
                txt = p.read_text(errors="replace")
                print(txt[:4000])
                if len(txt) > 4000:
                    print("... [truncated]")
            except Exception as e:
                print(f"Could not read text: {type(e).__name__}: {e}")
else:
    print("No benchmark directory")

print("\nCurrent pred_results contents:")
pred = Path("pred_results")
pred.mkdir(exist_ok=True)
for p in sorted(pred.iterdir()):
    print(" -", p, p.stat().st_size if p.is_file() else "dir")