#!/usr/bin/env python3
"""
Reclassify the MountainLionNew landCover and Protected_Status rasters using
the provided categorical mappings, saving outputs to pred_results/.
"""
from pathlib import Path
import sys
import numpy as np

try:
    import rasterio
except Exception as e:
    print("ERROR: rasterio could not be imported:", repr(e))
    sys.exit(1)

# The benchmark directory in this environment is exposed as ./benchmark.
base = Path("benchmark/datasets/MountainLionNew")
if not base.exists():
    # Fallback to resolved absolute path observed during inspection.
    base = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/MountainLionNew")

landcover_src = base / "landCover.tif"
protected_src = base / "Protected_Status.tif"

out_dir = Path("pred_results")
out_dir.mkdir(parents=True, exist_ok=True)
landcover_out = out_dir / "landCover_reclassified.tif"
protected_out = out_dir / "protected_status_reclassified.tif"

landCover_classification = {
    11: 10,  # Open Water
    21: 8,   # Developed, Open Space
    22: 7,   # Developed, Low Intensity
    23: 8,   # Developed, Medium Intensity
    24: 9,   # Developed, High Intensity
    31: 6,   # Barren Land
    41: 2,   # Deciduous Forest
    42: 1,   # Evergreen Forest
    43: 2,   # Mixed Forest
    52: 3,   # Shrub/Scrub
    71: 3,   # Grassland/Herbaceous
    72: 3,   # Sedge/Herbaceous
    81: 4,   # Hay/Pasture
    82: 6,   # Cultivated Crops
    90: 4,   # Woody Wetlands
    95: 4,   # Emergent Herbaceous Wetlands
    255: 10
}

protected_status_classification = {
    0: 1,
    1: 3,
    2: 6,
    3: 9,
    4: 10,
    255: 10
}

def reclassify_raster(src_path: Path, dst_path: Path, mapping: dict, default_value: int = 255):
    if not src_path.exists():
        raise FileNotFoundError(f"Input raster not found: {src_path}")

    with rasterio.open(src_path) as src:
        profile = src.profile.copy()
        data = src.read(1)
        unique_in = np.unique(data)

        print(f"\nReclassifying: {src_path}")
        print(f"  Dimensions: {src.width} x {src.height}")
        print(f"  CRS: {src.crs}")
        print(f"  Transform: {src.transform}")
        print(f"  Source dtype: {src.dtypes[0]}, nodata: {src.nodata}")
        print(f"  Unique input values ({len(unique_in)}): {unique_in.tolist()}")

        out = np.full(data.shape, default_value, dtype=np.uint8)
        for old_value, new_value in mapping.items():
            out[data == old_value] = new_value

        unmapped = sorted(int(v) for v in unique_in if int(v) not in mapping)
        if unmapped:
            print(f"  WARNING: Unmapped values were assigned {default_value}: {unmapped}")
        else:
            print("  All observed input values were mapped.")

        unique_out, counts_out = np.unique(out, return_counts=True)
        counts_dict = {int(v): int(c) for v, c in zip(unique_out, counts_out)}
        print(f"  Output value counts: {counts_dict}")

        profile.update(
            driver="GTiff",
            dtype=rasterio.uint8,
            count=1,
            compress="lzw",
            nodata=None
        )

        with rasterio.open(dst_path, "w", **profile) as dst:
            dst.write(out, 1)

    with rasterio.open(dst_path) as check:
        check_arr = check.read(1)
        print(f"  Saved: {dst_path}")
        print(f"  Verified dtype: {check_arr.dtype}")
        print(f"  Verified dimensions: {check.width} x {check.height}")
        print(f"  Verified min/max: {int(check_arr.min())}/{int(check_arr.max())}")
        print(f"  File size: {dst_path.stat().st_size} bytes")

print("Using dataset directory:", base)
reclassify_raster(landcover_src, landcover_out, landCover_classification)
reclassify_raster(protected_src, protected_out, protected_status_classification)

print("\nFinished reclassification.")
print("Required output exists:", landcover_out, landcover_out.exists())
print("Protected-status output exists:", protected_out, protected_out.exists())