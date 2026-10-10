#!/usr/bin/env python3
"""
Locate dataset files, then reclassify land cover and protected status rasters.

Outputs:
  pred_results/landCover_reclassified.tif
  pred_results/protected_status_reclassified.tif
"""

from pathlib import Path
import sys
import os
import numpy as np

try:
    import rasterio
except Exception as e:
    print("ERROR: rasterio could not be imported:", repr(e))
    sys.exit(1)


OUT_DIR = Path("pred_results")
OUT_DIR.mkdir(exist_ok=True)

landCover_classification = {
    11: 10,
    21: 8,
    22: 7,
    23: 8,
    24: 9,
    31: 6,
    41: 2,
    42: 1,
    43: 2,
    52: 3,
    71: 3,
    72: 3,
    81: 4,
    82: 6,
    90: 4,
    95: 4,
    255: 10,
}

protected_status_classification = {
    0: 1,
    1: 3,
    2: 6,
    3: 9,
    4: 10,
    255: 10,
}


def find_file(filename):
    """Find filename in likely mounted working/data directories."""
    candidates = []

    # Direct and common relative locations
    for base in [
        Path("."),
        Path("dataset"),
        Path("data"),
        Path("input"),
        Path("/data"),
        Path("/mnt/data"),
        Path("/tmp"),
    ]:
        p = base / filename
        if p.exists():
            candidates.append(p)
        p2 = base / "MountainLionNew" / filename
        if p2.exists():
            candidates.append(p2)

    # Search limited likely trees
    search_roots = [Path.cwd(), Path("/data/lab"), Path("/data"), Path("/mnt/data")]
    seen_roots = set()
    for root in search_roots:
        try:
            root_resolved = root.resolve()
        except Exception:
            continue
        if root_resolved in seen_roots or not root.exists():
            continue
        seen_roots.add(root_resolved)
        try:
            for p in root.rglob(filename):
                candidates.append(p)
        except Exception as e:
            print(f"Search warning for {root}: {e}")

    # Deduplicate while preserving order
    unique = []
    seen = set()
    for p in candidates:
        try:
            key = p.resolve()
        except Exception:
            key = p
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique


def print_environment():
    print("Working directory:", Path.cwd())
    print("Top-level current directory listing:")
    for p in sorted(Path(".").iterdir()):
        print(" ", p, "DIR" if p.is_dir() else "FILE")
    print("\nSearching for required rasters...")


def summarize_array(name, arr):
    vals, counts = np.unique(arr, return_counts=True)
    print(f"\n{name}:")
    print(f"  shape={arr.shape}, dtype={arr.dtype}, min={arr.min()}, max={arr.max()}")
    print(f"  unique_count={len(vals)}")
    if len(vals) <= 100:
        print(f"  unique values/counts={list(zip(vals.tolist(), counts.tolist()))}")
    else:
        print(f"  first 100 unique values/counts={list(zip(vals.tolist(), counts.tolist()))[:100]}")


def build_uint8_lut(mapping, default_value=0):
    lut = np.full(256, default_value, dtype=np.uint8)
    for old, new in mapping.items():
        lut[int(old)] = np.uint8(new)
    return lut


def reclassify_raster(src_path, out_path, mapping, default_value, label):
    print(f"\n--- Reclassifying {label} ---")
    print(f"Source: {src_path}")
    print(f"Output: {out_path}")

    with rasterio.open(src_path) as src:
        print(f"  driver={src.driver}, crs={src.crs}, transform={src.transform}")
        print(f"  width={src.width}, height={src.height}, count={src.count}, dtype={src.dtypes}, nodata={src.nodata}")
        if src.count != 1:
            raise ValueError(f"{src_path} has {src.count} bands; expected one.")

        arr = src.read(1)
        summarize_array(f"{label} source", arr)

        unique_vals = set(np.unique(arr).astype(int).tolist())
        unmapped = sorted(v for v in unique_vals if v not in mapping)
        print(f"  Unmapped source values (assigned default {default_value}): {unmapped}")

        if arr.min() < 0 or arr.max() > 255:
            raise ValueError(f"{label} values outside 0..255; cannot apply uint8 lookup safely.")
        lut = build_uint8_lut(mapping, default_value)
        rec = lut[arr.astype(np.uint8)]

        summarize_array(f"{label} reclassified", rec)

        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            dtype="uint8",
            count=1,
            nodata=None,
            compress="lzw",
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(rec, 1)

    with rasterio.open(out_path) as chk:
        chk_arr = chk.read(1)
        print(f"Verified output written: {out_path}")
        print(f"  crs={chk.crs}, transform={chk.transform}, dtype={chk.dtypes}, nodata={chk.nodata}")
        summarize_array(f"{label} output verification", chk_arr)


def main():
    print_environment()

    land_matches = find_file("landCover.tif")
    prot_matches = find_file("Protected_Status.tif")

    print("\nlandCover.tif matches:")
    for p in land_matches:
        print(" ", p)
    print("\nProtected_Status.tif matches:")
    for p in prot_matches:
        print(" ", p)

    if not land_matches:
        raise FileNotFoundError("Could not locate landCover.tif")
    if not prot_matches:
        raise FileNotFoundError("Could not locate Protected_Status.tif")

    # Prefer paths inside MountainLionNew if multiple, otherwise first match.
    land_src = next((p for p in land_matches if "MountainLionNew" in p.parts), land_matches[0])
    prot_src = next((p for p in prot_matches if "MountainLionNew" in p.parts), prot_matches[0])

    reclassify_raster(
        land_src,
        OUT_DIR / "landCover_reclassified.tif",
        landCover_classification,
        default_value=0,   # landCover has background 0 not included in the supplied classification.
        label="landCover",
    )

    reclassify_raster(
        prot_src,
        OUT_DIR / "protected_status_reclassified.tif",
        protected_status_classification,
        default_value=0,
        label="protected_status",
    )

    print("\nDONE")
    print("Required output:", OUT_DIR / "landCover_reclassified.tif", "exists=", (OUT_DIR / "landCover_reclassified.tif").exists())
    print("Additional output:", OUT_DIR / "protected_status_reclassified.tif", "exists=", (OUT_DIR / "protected_status_reclassified.tif").exists())


if __name__ == "__main__":
    main()