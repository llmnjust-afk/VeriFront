import os
import glob

print("Working dir:", os.getcwd())
print("Top-level entries:", sorted(os.listdir("."))[:200])

# Search nearby for the dataset folder/files
patterns = [
    "CogSci_pattern_high_sim_data",
    "*/CogSci_pattern_high_sim_data",
    "*/*/CogSci_pattern_high_sim_data",
    "/data/lab/VeriFront/**/CogSci_pattern_high_sim_data",
]
found = []
for pat in patterns:
    found.extend(glob.glob(pat, recursive=True))
found = sorted(set(found))
print("Found dataset dirs:", found)

# Also search for signature files
sig = sorted(glob.glob("/data/lab/VeriFront/**/Atmosphere.csv", recursive=True))[:50]
print("Atmosphere.csv candidates:", sig)

if found:
    base = found[0]
    print("Using base:", base)
    print("Files:", sorted(os.listdir(base)))
else:
    print("Dataset folder not found in searched locations.")