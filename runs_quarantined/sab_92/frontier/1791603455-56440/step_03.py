#!/usr/bin/env python3
from pathlib import Path
import os

def safe_list(path, max_items=80):
    print(f"\nListing: {path}")
    try:
        items = list(Path(path).iterdir())
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        return
    for item in items[:max_items]:
        kind = "dir" if item.is_dir() else "file"
        extra = ""
        try:
            if item.is_symlink():
                extra += f" -> {os.readlink(item)}"
            if item.is_file():
                extra += f" ({item.stat().st_size} bytes)"
        except Exception as e:
            extra += f" [stat/readlink error: {e}]"
        print(f"  {kind}: {item.name}{extra}")
    if len(items) > max_items:
        print(f"  ... {len(items)-max_items} more")

def main():
    cwd = Path.cwd()
    print("cwd:", cwd)
    for p in [cwd, cwd/"benchmark", cwd/"benchmark"/"jnmf_visualization", cwd/"benchmark"/"data", cwd.parent, Path("/data/lab/VeriFront")]:
        safe_list(p)

    print("\nSearching cwd for .npy files (limited):")
    count = 0
    for p in cwd.rglob("*.npy"):
        print(" ", p)
        count += 1
        if count >= 100:
            print(" ... stopped at 100")
            break
    print("npy count shown:", count)

    print("\nSearching benchmark for relevant names (limited):")
    count = 0
    bench = cwd / "benchmark"
    if bench.exists():
        for p in bench.rglob("*"):
            name = p.name.lower()
            if "jnmf" in name or "conscientiousness" in name or name.endswith(".npy"):
                print(" ", p, "dir" if p.is_dir() else "file")
                count += 1
                if count >= 200:
                    print(" ... stopped at 200")
                    break
    print("relevant count shown:", count)

if __name__ == "__main__":
    main()