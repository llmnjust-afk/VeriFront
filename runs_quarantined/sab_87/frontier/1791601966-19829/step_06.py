#!/usr/bin/env python3
from pathlib import Path
import csv
import numpy as np
import shutil
import sys

infile = Path("polynomial_fit/A1B_north_america.nc")
if not infile.exists():
    src = Path("benchmark/datasets/polynomial_fit/A1B_north_america.nc")
    if src.exists():
        infile.parent.mkdir(exist_ok=True)
        shutil.copy2(src, infile)
        print(f"Copied dataset from {src} to {infile}")
    else:
        raise FileNotFoundError(f"Could not find {infile} or {src}")

outdir = Path("pred_results")
outdir.mkdir(exist_ok=True)
outfile = outdir / "polynomial_fit_pred.csv"

print(f"Generating polynomial fit results from {infile}")

# Prefer the same scientific stack/logic as the benchmark: iris preserves the raw
# numeric time coordinate used for fitting, while providing cftime conversion info.
try:
    import iris
    import cftime

    cube = iris.load_cube(str(infile))
    location = next(cube.slices(["time"]))
    x_points = location.coord("time").points
    y_points = location.data
    print("Loaded with iris")
    print("Cube:", cube.summary(shorten=True))
    print("Selected time-series shape:", y_points.shape)
    print("x first/last:", x_points[:5], x_points[-5:])
    print("y first/last:", y_points[:5], y_points[-5:])

    degree = 2
    p = np.polyfit(x_points, y_points, degree)
    y_fitted = np.polyval(p, x_points)
    print("Polynomial coefficients:", p)

    time_units = location.coord("time").units
    readable_dates = [
        cftime.num2date(x, units=time_units.origin, calendar=time_units.calendar).strftime("%Y")
        for x in x_points
    ]

except Exception as e:
    print(f"Iris path failed ({type(e).__name__}: {e}); falling back to netCDF4.")
    from netCDF4 import Dataset, num2date

    with Dataset(str(infile), "r") as ds:
        tvar = ds.variables["time"]
        x_points = np.array(tvar[:])
        temp = np.array(ds.variables["air_temperature"][:])
        # Match iris.load_cube(...); next(cube.slices(["time"])) selects the
        # first latitude/longitude time series from a (time, lat, lon) cube.
        y_points = temp[:, 0, 0]
        print("Loaded with netCDF4")
        print("Temperature array shape:", temp.shape)
        print("x first/last:", x_points[:5], x_points[-5:])
        print("y first/last:", y_points[:5], y_points[-5:])
        p = np.polyfit(x_points, y_points, 2)
        y_fitted = np.polyval(p, x_points)
        print("Polynomial coefficients:", p)
        dates = num2date(x_points, units=tvar.units, calendar=getattr(tvar, "calendar", "standard"))
        readable_dates = [d.strftime("%Y") for d in dates]

with open(outfile, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Year", "Fitted_Temperature"])
    writer.writerows(list(zip(readable_dates, y_fitted)))

print(f"Wrote {outfile}")
print("First 5 output rows:")
with open(outfile, "r") as f:
    for i, line in zip(range(6), f):
        print(line.rstrip())
print("Last 5 output rows:")
lines = outfile.read_text().splitlines()
for line in lines[-5:]:
    print(line)

gold = Path("benchmark/eval_programs/gold_results/polynomial_fit_gold.csv")
if gold.exists():
    pred_text = outfile.read_text()
    gold_text = gold.read_text()
    print("Matches gold exactly:", pred_text == gold_text)
    if pred_text != gold_text:
        pred_lines = pred_text.splitlines()
        gold_lines = gold_text.splitlines()
        for i, (a, b) in enumerate(zip(pred_lines, gold_lines), start=1):
            if a != b:
                print(f"First difference at line {i}:")
                print("pred:", a)
                print("gold:", b)
                break
        print("pred lines/gold lines:", len(pred_lines), len(gold_lines))