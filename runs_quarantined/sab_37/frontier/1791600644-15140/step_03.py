import os
from pathlib import Path

print("CWD:", os.getcwd())

for base in [Path("benchmark"), Path("/data/lab/VeriFront"), Path("/data/lab")]:
    print(f"\nListing/searching under {base} (exists={base.exists()}):")
    if base.exists():
        count = 0
        for root, dirs, files in os.walk(base):
            # avoid very deep / huge traversal
            rel_parts = Path(root).relative_to(base).parts if root != str(base) else ()
            if len(rel_parts) > 6:
                dirs[:] = []
                continue
            if count < 50:
                print("DIR", root, "subdirs", dirs[:5], "nfiles", len(files))
            count += 1
            for f in files:
                low = f.lower()
                if ("mist" in low or "hr" in low or low.endswith((".xlsx", ".xls", ".csv", ".tsv"))):
                    p = Path(root) / f
                    try:
                        sz = p.stat().st_size
                    except Exception:
                        sz = "?"
                    print("  MATCH", p, "size", sz)
        print("Visited dirs:", count)