#!/usr/bin/env python3
"""
Reclassify land cover and protected status rasters to a common 1-10 scale.

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
    print("ERROR: rasterio is required for this geospatial raster task but could not be imported.")
    print(repr(e))
    sys.exit(1)


DATA_DIR = Path("MountainLionNew")
OUT_DIR = Path("pred_results")
OUT_DIR.mkdir(exist_ok=True)

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


def summarize_array(name, arr):
    vals, counts = np.unique(arr, return_counts=True)
    pairs = list(zip(vals.tolist(), counts.tolist()))
    print(f"\n{name}:")
    print(f"  shape={arr.shape}, dtype={arr.dtype}")
    print(f"  min={arr.min()}, max={arr.max()}")
    print(f"  unique_count={len(vals)}")
    print(f"  unique values/counts={pairs[:50]}{' ...' if len(pairs) > 50 else ''}")


def build_uint8_lut(mapping, default_value=0):
    lut = np.full(256, default_value, dtype=np.uint8)
    for old, new in mapping.items():
        if not (0 <= old <= 255 and 0 <= new <= 255):
            raise ValueError(f"Mapping values must fit uint8: {old}->{new}")
        lut[old] = new
    return lut


def reclassify_raster(src_path, out_path, mapping, default_value=0, label="raster"):
    if not src_path.exists():
        raise FileNotFoundError(f"Missing source raster: {src_path}")

    with rasterio.open(src_path) as src:
        profile = src.profile.copy()
        print(f"\nReading {label}: {src_path}")
        print(f"  CRS={src.crs}")
        print(f"  transform={src.transform}")
        print(f"  nodata={src.nodata}")
        print(f"  width={src.width}, height={src.height}, count={src.count}")

        if src.count != 1:
            raise ValueError(f"Expected single-band raster for {src_path}, found {src.count} bands")

        arr = src.read(1)
        summarize_array(f"{label} source", arr)

        unique_vals = set(np.unique(arr).astype(int).tolist())
        unmapped = sorted(v for v in unique_vals if v not in mapping)
        print(f"  source values not explicitly in classification dictionary: {unmapped}")

        if arr.dtype != np.uint8:
            print(f"  NOTE: source dtype is {arr.dtype}; converting through integer indexing after validation.")
            if arr.min() < 0 or arr.max() > 255:
                raise ValueError(f"{src_path} has values outside 0..255; cannot use uint8 lookup table safely.")
            arr_index = arr.astype(np.uint8)
        else:
            arr_index = arr

        lut = build_uint8_lut(mapping, default_value=default_value)
        rec = lut[arr_index]
        summarize_array(f"{label} reclassified", rec)

        profile.update(
            driver="GTiff",
            dtype=rasterio.uint8,
            count=1,
            compress="lzw",
            nodata=None
        )

        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(rec, 1)

    with rasterio.open(out_path) as chk:
        out_arr = chk.read(1)
        print(f"\nWrote {label} output: {out_path}")
        print(f"  output CRS={chk.crs}")
        print(f"  output transform={chk.transform}")
        print(f"  output nodata={chk.nodata}")
        summarize_array(f"{label} output verification", out_arr)


def compare_existing_if_present(existing_path, new_path, label):
    if not existing_path.exists():
        print(f"\nNo existing benchmark-like file found for {label}: {existing_path}")
        return
    with rasterio.open(existing_path) as ex, rasterio.open(new_path) as nw:
        ex_arr = ex.read(1)
        nw_arr = nw.read(1)
        same_shape = ex_arr.shape == nw_arr.shape
        same = same_shape and np.array_equal(ex_arr, nw_arr)
        print(f"\nComparison with existing {label} file in dataset folder:")
        print(f"  existing path={existing_path}")
        print(f"  same_shape={same_shape}, exact_array_match={same}")
        if same_shape and not same:
            diff = ex_arr.astype(np.int16) - nw_arr.astype(np.int16)
            print(f"  differing_pixels={int(np.count_nonzero(diff))}")
            summarize_array(f"{label} existing values", ex_arr)
            summarize_array(f"{label} difference existing-minus-new", diff)


def main():
    print("Starting categorical raster standardization/reclassification.")
    print(f"Working directory: {Path.cwd()}")
    print(f"Dataset directory exists: {DATA_DIR.exists()}")

    land_src = DATA_DIR / "landCover.tif"
    prot_src = DATA_DIR / "Protected_Status.tif"

    land_out = OUT_DIR / "landCover_reclassified.tif"
    prot_out = OUT_DIR / "protected_status_reclassified.tif"

    # landCover has value 0 in the preview but no class dictionary entry.
    # Treat unmapped values as 0 (background/NoData-like) while applying all provided mappings.
    reclassify_raster(
        land_src,
        land_out,
        landCover_classification,
        default_value=0,
        label="landCover"
    )

    # Protected status dictionary explicitly maps 0 to 1.
    reclassify_raster(
        prot_src,
        prot_out,
        protected_status_classification,
        default_value=0,
        label="protected_status"
    )

    compare_existing_if_present(DATA_DIR / "landcover_reclassified.tif", land_out, "landCover")
    compare_existing_if_present(DATA_DIR / "protected_status_reclassified.tif", prot_out, "protected_status")

    print("\nDONE")
    print(f"Required output present: {land_out.exists()} -> {land_out}")
    print(f"Additional output present: {prot_out.exists()} -> {prot_out}")


if __name__ == "__main__":
    main()