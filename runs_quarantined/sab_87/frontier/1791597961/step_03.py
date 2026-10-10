#!/usr/bin/env python3
from pathlib import Path
import os, json

print("Inspecting benchmark directory...")
for p in sorted(Path("benchmark").rglob("*")):
    try:
        rel = p
        if p.is_dir():
            print("DIR ", rel)
        else:
            print("FILE", rel, p.stat().st_size, "bytes")
            if p.stat().st_size < 20000 and p.suffix.lower() in [".py", ".txt", ".json", ".yaml", ".yml", ".md", ".csv"]:
                print("---", rel, "content start ---")
                try:
                    print(p.read_text(errors="replace")[:4000])
                except Exception as e:
                    print("read failed", e)
                print("--- content end ---")
    except Exception as e:
        print("ERR", p, e)

print("\nEnvironment variables possibly relevant:")
for k, v in sorted(os.environ.items()):
    if any(s in k.lower() for s in ["data", "bench", "input", "path"]):
        print(k, "=", v)