import os
from pathlib import Path

print("Recursive listing of benchmark directory:")
base = Path("benchmark")
if base.exists():
    for root, dirs, files in os.walk(base):
        depth = len(Path(root).relative_to(base).parts)
        if depth > 5:
            dirs[:] = []
            continue
        indent = "  " * depth
        print(f"{indent}{Path(root).name}/")
        for f in files[:20]:
            fp = Path(root) / f
            print(f"{indent}  {f} ({fp.stat().st_size} bytes)")
        if len(files) > 20:
            print(f"{indent}  ... {len(files)-20} more files")
else:
    print("No benchmark directory found")

print("\nSearching broader /data/lab/VeriFront for saliva/data.pkl (limited):")
count = 0
for root, dirs, files in os.walk("/data/lab/VeriFront"):
    # prune likely irrelevant large dirs only if too deep? keep
    if "data.pkl" in files or Path(root).name == "saliva_data":
        print("FOUND:", root, "files:", files[:10])
        count += 1
        if count >= 20:
            break
print("Total reported:", count)