#!/usr/bin/env python3
import os
from pathlib import Path

base = Path("benchmark/datasets")
print("Inspecting", base, "exists", base.exists(), "is_dir", base.is_dir())
if base.exists():
    for root, dirs, files in os.walk(base, followlinks=True):
        level = Path(root).relative_to(base).parts
        depth = len(level)
        if depth > 4:
            dirs[:] = []
            continue
        indent = "  " * depth
        print(f"{indent}{Path(root).name}/")
        for d in dirs[:20]:
            dp = Path(root) / d
            print(f"{indent}  [D] {d}" + (" -> " + os.readlink(dp) if dp.is_symlink() else ""))
        for f in files[:30]:
            print(f"{indent}  [F] {f}")
        if len(files) > 30:
            print(f"{indent}  ... {len(files)-30} more files")

print("\nSearching benchmark for questionnaire/data pickle files:")
patterns = ["*questionnaire*", "*.pkl", "*.pickle", "*.csv"]
for pattern in patterns:
    print("Pattern:", pattern)
    count = 0
    for root, dirs, files in os.walk("benchmark", followlinks=True):
        for name in files + dirs:
            if Path(name).match(pattern):
                print(" ", Path(root) / name)
                count += 1
                if count >= 50:
                    print("  ... truncated")
                    break
        if count >= 50:
            break
    print(" count", count)