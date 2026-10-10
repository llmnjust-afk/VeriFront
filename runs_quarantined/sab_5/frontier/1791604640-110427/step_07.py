#!/usr/bin/env python3
from pathlib import Path

print("DKPES eval/gold/scoring files and relevant content")
for root in ["benchmark/eval_programs", "benchmark/scoring_rubrics", "benchmark/gold_programs"]:
    p = Path(root)
    if not p.exists():
        continue
    for f in p.rglob("*"):
        if f.is_file() and ("dkpes" in f.name.lower() or "dkpes" in str(f).lower()):
            print("\nFILE:", f, "size:", f.stat().st_size)
            txt = f.read_text(errors="ignore")
            # Print complete for small files, otherwise sections with output paths/columns.
            if len(txt) <= 12000:
                print(txt)
            else:
                for key in ["dkpes_test_pred", "Signal-inhibition", "RandomForest", "threshold", "accuracy", "pred_results"]:
                    idx = txt.lower().find(key.lower())
                    if idx >= 0:
                        print(f"\n--- around {key} ---")
                        print(txt[max(0, idx-1500):idx+3000])