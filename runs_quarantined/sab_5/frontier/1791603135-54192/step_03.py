import os
from pathlib import Path

print("Working directory:", os.getcwd())
print("Top-level entries with details:")
for p in Path(".").iterdir():
    try:
        print(p, "dir" if p.is_dir() else "file", "symlink" if p.is_symlink() else "", "size", p.stat().st_size)
    except Exception as e:
        print(p, "ERR", e)

print("\nBenchmark listing/details:")
bp = Path("benchmark")
if bp.exists():
    print("benchmark is_dir:", bp.is_dir(), "is_symlink:", bp.is_symlink(), "resolve:", bp.resolve())
    try:
        print("benchmark entries:", list(bp.iterdir())[:50])
    except Exception as e:
        print("Could not list benchmark:", repr(e))
else:
    print("No benchmark path")

print("\nSearching wider under /data/lab/VeriFront/runs/sab_5/frontier current parent levels:")
search_roots = [Path("."), Path(".."), Path("../.."), Path("/data/lab/VeriFront")]
seen = set()
for sr in search_roots:
    if not sr.exists():
        continue
    print("\nSEARCH ROOT", sr.resolve())
    count = 0
    try:
        for root, dirs, files in os.walk(sr):
            # avoid too deep/huge: prune hidden/cache and stop after finds
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".cache"}]
            depth = len(Path(root).resolve().parts) - len(sr.resolve().parts)
            if depth > 6:
                dirs[:] = []
                continue
            for f in files:
                lf = f.lower()
                if lf in ("dkpes_train.csv", "dkpes_test.csv") or "dkpes" in lf:
                    full = str(Path(root) / f)
                    if full not in seen:
                        print("FOUND", full)
                        seen.add(full)
                        count += 1
            if count >= 20:
                break
    except Exception as e:
        print("Search error:", repr(e))
    print("found count in root:", count)