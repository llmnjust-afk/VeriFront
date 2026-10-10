import os
import pandas as pd
from pathlib import Path

print("Working directory:", os.getcwd())
print("Top-level files:", os.listdir("."))

# Locate DKPES CSV files robustly
matches = []
for root, dirs, files in os.walk("."):
    for f in files:
        if f.lower() in ("dkpes_train.csv", "dkpes_test.csv") or "dkpes" in f.lower():
            matches.append(os.path.join(root, f))
print("DKPES-like files found:")
for m in matches:
    print(" ", m)

train_candidates = [m for m in matches if os.path.basename(m) == "dkpes_train.csv"]
test_candidates = [m for m in matches if os.path.basename(m) == "dkpes_test.csv"]

if not train_candidates or not test_candidates:
    print("\nDirectory tree preview:")
    for root, dirs, files in os.walk("."):
        level = root.count(os.sep)
        if level <= 3:
            print("  " * level + os.path.basename(root) + "/")
            for f in files[:10]:
                print("  " * (level + 1) + f)
    raise FileNotFoundError("Could not find dkpes_train.csv and dkpes_test.csv")

train_path = train_candidates[0]
test_path = test_candidates[0]
print("Using train:", train_path)
print("Using test:", test_path)

train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

print("Train shape:", train.shape)
print("Test shape:", test.shape)
print("Train columns:", list(train.columns))
print("Test columns:", list(test.columns))
print("\nTrain head:")
print(train.head().to_string())
print("\nTest head:")
print(test.head().to_string())

print("\nSignal-inhibition summary:")
print(train["Signal-inhibition"].describe(percentiles=[.05,.1,.2,.25,.3,.4,.5,.6,.7,.75,.8,.9,.95]).to_string())
print("\nMissing values train:")
print(train.isna().sum().to_string())
print("\nMissing values test:")
print(test.isna().sum().to_string())

if "ShapeQuery" in train.columns:
    print("\nUnique ShapeQuery train/test counts:", train["ShapeQuery"].nunique(), test["ShapeQuery"].nunique())
    print("Top ShapeQuery train:")
    print(train["ShapeQuery"].value_counts().head(10).to_string())

# Save discovered paths for next turn
Path("work_info").mkdir(exist_ok=True)
with open("work_info/dkpes_paths.txt", "w") as f:
    f.write(train_path + "\n" + test_path + "\n")
print("\nSaved paths to work_info/dkpes_paths.txt")