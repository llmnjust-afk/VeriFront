import os
from pathlib import Path

base = Path("benchmark/datasets")
print("benchmark/datasets exists:", base.exists(), "resolve:", base.resolve() if base.exists() else None)

if base.exists():
    print("\nFirst-level dataset entries:")
    entries = sorted(list(base.iterdir()), key=lambda p: p.name.lower())
    for p in entries[:200]:
        print(p.name, "dir" if p.is_dir() else "file")
    print("Total first-level entries:", len(entries))

    print("\nSearching benchmark/datasets for dkpes-like paths and CSVs with Signal-inhibition...")
    found_names = []
    csv_candidates = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
        for d in dirs:
            if "dkpes" in d.lower():
                found_names.append(str(Path(root)/d))
        for f in files:
            lf = f.lower()
            full = Path(root)/f
            if "dkpes" in lf:
                found_names.append(str(full))
            if lf.endswith(".csv"):
                csv_candidates.append(full)
    print("dkpes-like names found:", len(found_names))
    for x in found_names[:100]:
        print("DKPESLIKE", x)

    print("Total CSV candidates:", len(csv_candidates))
    matches = []
    for i, csv in enumerate(csv_candidates):
        try:
            with open(csv, "r", errors="ignore") as fh:
                header = fh.readline().strip()
            if "Signal-inhibition" in header or "Signal" in header or "inhibition" in header.lower():
                matches.append((csv, header[:300]))
        except Exception as e:
            pass
    print("CSV header matches:", len(matches))
    for csv, header in matches[:100]:
        print("MATCH", csv)
        print(" HEADER", header)
else:
    print("No datasets directory")