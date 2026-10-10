#!/usr/bin/env python3
import csv
from pathlib import Path
import shutil
import numpy as np
import netCDF4

# Ensure the dataset is present at the task-specified relative path.
local_nc = Path("polynomial_fit/A1B_north_america.nc")
if not local_nc.exists():
    src = Path("/data/lab/sab_data/benchmark_verified/benchmark/datasets/polynomial_fit/A1B_north_america.nc")
    local_nc.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, local_nc)
    print(f"Copied dataset to {local_nc}")

# Load NetCDF data.
ds = netCDF4.Dataset(local_nc, "r")
print("Variables:")
for name, var in ds.variables.items():
    print(f"  {name}: dims={var.dimensions}, shape={var.shape}, dtype={var.dtype}")
    attrs = {a: getattr(var, a) for a in var.ncattrs()}
    print(f"    attrs={attrs}")

# Identify time and temperature variables.
time = np.asarray(ds.variables["time"][:], dtype=float)
if "air_temperature" in ds.variables:
    temp_var = ds.variables["air_temperature"]
elif "tas" in ds.variables:
    temp_var = ds.variables["tas"]
else:
    candidates = [v for v in ds.variables if v != "time" and np.asarray(ds.variables[v].shape).size > 0]
    temp_var = ds.variables[candidates[0]]

temp = temp_var[:]
print(f"Selected temperature variable: {temp_var.name}, shape={temp.shape}")

# Match Iris next(cube.slices(['time'])): take the first point in all non-time dimensions.
# For the known data this is equivalent to air_temperature[:, 0, 0].
time_dim_index = temp_var.dimensions.index("time")
arr = np.ma.asarray(temp)
if time_dim_index != 0:
    arr = np.moveaxis(arr, time_dim_index, 0)
idx = (slice(None),) + tuple(0 for _ in range(arr.ndim - 1))
y_points = np.asarray(arr[idx], dtype=float)

print("First time values:", time[:5].tolist())
print("First temperature-series values:", y_points[:5].tolist())
print("Series length:", len(time), len(y_points))

# Quadratic polynomial fit and fitted values at the original time points.
degree = 2
coef = np.polyfit(time, y_points, degree)
y_fitted = np.polyval(coef, time)
print("Polynomial coefficients:", coef.tolist())
print("First fitted values:", y_fitted[:5].tolist())

# Convert annual 360-day calendar time axis to years.
# The file uses hours since 1970-01-01 00:00:00 with a 360_day calendar; use netCDF4 if possible.
time_units = getattr(ds.variables["time"], "units", None)
calendar = getattr(ds.variables["time"], "calendar", "standard")
try:
    dates = netCDF4.num2date(time, units=time_units, calendar=calendar)
    years = [d.strftime("%Y") for d in dates]
except Exception as e:
    print("num2date conversion failed, using known annual 360-day fallback:", repr(e))
    years = [str(int(round(1970 + t / (24 * 360)))) for t in time]

ds.close()

# Write required CSV.
out_path = Path("pred_results/polynomial_fit_pred.csv")
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Year", "Fitted_Temperature"])
    writer.writerows(zip(years, y_fitted))

print(f"Wrote {out_path} with {len(years)} data rows")
print("CSV preview:")
with out_path.open("r") as f:
    for i, line in zip(range(8), f):
        print(line.rstrip())