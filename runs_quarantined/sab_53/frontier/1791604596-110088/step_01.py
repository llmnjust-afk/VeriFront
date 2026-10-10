#!/usr/bin/env python3
"""
Reclassify land cover and protected status rasters to common suitability scales
for mountain lion habitat analysis.

Outputs:
  pred_results/landCover_reclassified.tif
  pred_results/protected_status_reclassified.tif
"""
from pathlib import Path
import sys
import numpy as np

try:
    import rasterio
except Exception as e:
    print("ERROR: rasterio is required but could not be imported:", repr(e))
    sys.exit(1)

base = Path("MountainLionNew")
out_dir = Path("pred_results")
out_dir.mkdir(parents=True, exist_ok=True)

landcover_src = base / "landCover.tif"
protected_src = base / "Protected_Status.tif"

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
        print(f"\nReading {src_path}")
        print(f"  shape: ({src.height}, {src.width}), count: {src.count}, dtype: {src.dtypes[0]}")
        print(f"  crs: {src.crs}")
        print(f"  transform: {src.transform}")
        if src.nodata is not None:
            print(f"  source nodata: {src.nodata}")

        data = src.read(1)
        unique_in = np.unique(data)
        print(f"  unique input values ({len(unique_in)}): {unique_in[:80]}{' ...' if len(unique_in) > 80 else ''}")

        out = np.full(data.shape, default_value, dtype=np.uint8)
        for in_val, out_val in mapping.items():
            out[data == in_val] = out_val

        unmapped = sorted(int(v) for v in unique_in if int(v) not in mapping)
        if unmapped:
            print(f"  WARNING: unmapped input values assigned default {default_value}: {unmapped}")
        else:
            print("  all input values were mapped")

        unique_out, counts_out = np.unique(out, return_counts=True)
        print("  output value counts:")
        for val, cnt in zip(unique_out, counts_out):
            print(f"    {int(val):3d}: {int(cnt)}")

        profile.update(
            dtype=rasterio.uint8,
            count=1,
            compress="lzw",
            nodata=None
        )

        with rasterio.open(dst_path, "w", **profile) as dst:
            dst.write(out, 1)

    with rasterio.open(dst_path) as chk:
        arr = chk.read(1)
        print(f"Saved {dst_path}")
        print(f"  verified shape: ({chk.height}, {chk.width}), dtype: {arr.dtype}, crs: {chk.crs}")
        print(f"  verified min/max: {int(arr.min())}/{int(arr.max())}")
        print(f"  file size bytes: {dst_path.stat().st_size}")

reclassify_raster(landcover_src, landcover_out, landCover_classification)
reclassify_raster(protected_src, protected_out, protected_status_classification)

print("\nReclassification complete.")
print(f"Required output written: {landcover_out}")
print(f"Additional output written: {protected_out}")