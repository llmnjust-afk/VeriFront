#!/usr/bin/env python3
"""
Locate available dataset files, then reclassify land cover and protected status rasters.
This turn diagnoses the actual working-directory layout and attempts robust path discovery.
"""
from pathlib import Path
import sys
import numpy as np

try:
    import rasterio
except Exception as e:
    print("ERROR: rasterio import failed:", repr(e))
    sys.exit(1)

print("Current working directory:", Path.cwd())
print("\nTop-level directory listing:")
for p in sorted(Path(".").iterdir()):
    print(" ", "DIR " if p.is_dir() else "FILE", p)

print("\nSearching for relevant TIFF files:")
all_tifs = sorted(Path(".").rglob("*.tif"))
for p in all_tifs:
    print(" ", p)

def find_one(candidates):
    for c in candidates:
        matches = sorted(Path(".").rglob(c))
        if matches:
            return matches[0]
    return None

landcover_src = find_one(["landCover.tif", "landcover.tif", "*landCover*.tif", "*landcover*.tif"])
protected_src = find_one(["Protected_Status.tif", "protected_status.tif", "*Protected*Status*.tif", "*protected*status*.tif"])

print("\nDiscovered paths:")
print(" landcover_src =", landcover_src)
print(" protected_src =", protected_src)

if landcover_src is None or protected_src is None:
    print("ERROR: Could not find both required source rasters.")
    sys.exit(1)

out_dir = Path("pred_results")
out_dir.mkdir(parents=True, exist_ok=True)
landcover_out = out_dir / "landCover_reclassified.tif"
protected_out = out_dir / "protected_status_reclassified.tif"

landCover_classification = {
    11: 10, 21: 8, 22: 7, 23: 8, 24: 9, 31: 6, 41: 2, 42: 1, 43: 2,
    52: 3, 71: 3, 72: 3, 81: 4, 82: 6, 90: 4, 95: 4, 255: 10
}
protected_status_classification = {0: 1, 1: 3, 2: 6, 3: 9, 4: 10, 255: 10}

def reclassify_raster(src_path: Path, dst_path: Path, mapping: dict, default_value: int = 255):
    with rasterio.open(src_path) as src:
        profile = src.profile.copy()
        data = src.read(1)
        unique_in = np.unique(data)

        print(f"\nSource: {src_path}")
        print(f" shape=({src.height}, {src.width}) dtype={src.dtypes[0]} crs={src.crs}")
        print(f" nodata={src.nodata} transform={src.transform}")
        print(f" unique input values ({len(unique_in)}): {unique_in.tolist()}")

        out = np.full(data.shape, default_value, dtype=np.uint8)
        for in_val, out_val in mapping.items():
            out[data == in_val] = out_val

        unmapped = sorted(int(v) for v in unique_in if int(v) not in mapping)
        if unmapped:
            print(f" WARNING: unmapped values assigned {default_value}: {unmapped}")
        else:
            print(" all input values mapped")

        vals, counts = np.unique(out, return_counts=True)
        print(" output counts:", {int(v): int(c) for v, c in zip(vals, counts)})

        profile.update(dtype=rasterio.uint8, count=1, compress="lzw", nodata=None)
        with rasterio.open(dst_path, "w", **profile) as dst:
            dst.write(out, 1)

    with rasterio.open(dst_path) as chk:
        arr = chk.read(1)
        print(f" Saved: {dst_path}")
        print(f" verified shape=({chk.height}, {chk.width}) dtype={arr.dtype} min={int(arr.min())} max={int(arr.max())}")
        print(f" size={dst_path.stat().st_size} bytes")

reclassify_raster(landcover_src, landcover_out, landCover_classification)
reclassify_raster(protected_src, protected_out, protected_status_classification)

print("\nDONE")
print("Required output:", landcover_out, "exists=", landcover_out.exists())
print("Additional output:", protected_out, "exists=", protected_out.exists())