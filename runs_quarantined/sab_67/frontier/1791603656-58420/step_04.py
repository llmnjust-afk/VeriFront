from pathlib import Path
import os, re
import pandas as pd
import numpy as np

cwd = Path.cwd()
bench = cwd / "benchmark"
print("Searching for CogSci-related paths/files under benchmark...")
matches = []
for p in bench.rglob("*"):
    s = str(p.relative_to(bench))
    if "CogSci" in s or "cog" in s.lower() or "syllog" in s.lower() or "conscient" in s.lower() or "openness" in s.lower():
        matches.append(p)
for p in sorted(matches):
    print(("DIR " if p.is_dir() else "FILE"), p.relative_to(cwd), ("" if p.is_dir() else f"{p.stat().st_size} bytes"))

print("\nInspect all small CSVs potentially relevant (<= 1MB) with columns/head:")
csvs = [p for p in bench.rglob("*.csv") if p.stat().st_size <= 1_000_000]
for p in sorted(csvs):
    try:
        df = pd.read_csv(p, nrows=5)
        cols = list(df.columns)
        if any(c in cols for c in ["Syllogism", "Prediction", "conscientiousness", "openness"]) or "CogSci" in str(p):
            print("\nCSV", p.relative_to(cwd), p.stat().st_size, "cols", cols)
            print(df.to_string(index=False))
    except Exception as e:
        pass

print("\nSearching source/text files for CogSci_pattern_high_sim_data references...")
for ext in ["*.py", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"]:
    for p in bench.rglob(ext):
        try:
            txt = p.read_text(errors="ignore")
        except:
            continue
        if "CogSci_pattern_high_sim" in txt or "conscientiousness" in txt or "openness" in txt or "Syllogism" in txt:
            print("\n---", p.relative_to(cwd), "---")
            # print relevant lines
            lines = txt.splitlines()
            for i, line in enumerate(lines):
                if any(term in line for term in ["CogSci_pattern_high_sim", "conscientiousness", "openness", "Syllogism", "Prediction"]):
                    start = max(0, i-2); end = min(len(lines), i+3)
                    for j in range(start, end):
                        print(f"{j+1}: {lines[j]}")
                    print("...")
                    break