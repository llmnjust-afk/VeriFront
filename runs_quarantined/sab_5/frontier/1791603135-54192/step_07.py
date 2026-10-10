import os
from pathlib import Path

print("Inspecting benchmark task-related files for expected output format or DKPES reference programs...")
for root, dirs, files in os.walk("benchmark"):
    dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
    for f in files:
        lf = f.lower()
        full = Path(root) / f
        if "dkpes" in lf or "dkpes" in str(full).lower():
            print("FOUND", full)

print("\nLooking for pred_results mentions and dkpes in eval/gold/scoring files...")
keywords = ["dkpes", "pred_results", "dkpes_test_pred", "Signal-inhibition"]
for sub in ["benchmark/gold_programs", "benchmark/eval_programs", "benchmark/scoring_rubrics", "benchmark/README.md"]:
    p = Path(sub)
    if not p.exists():
        continue
    if p.is_file():
        files = [p]
    else:
        files = [Path(r)/f for r, ds, fs in os.walk(p) for f in fs if f.endswith((".py",".md",".txt",".json",".yaml",".yml"))]
    for file in files:
        try:
            txt = file.read_text(errors="ignore")
        except Exception:
            continue
        low = txt.lower()
        if any(k.lower() in low for k in keywords):
            print("\n---", file, "---")
            lines = txt.splitlines()
            for i, line in enumerate(lines):
                if any(k.lower() in line.lower() for k in keywords):
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    for j in range(start, end):
                        print(f"{j+1}: {lines[j]}")
                    print("...")