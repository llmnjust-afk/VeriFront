from pathlib import Path
import json

files = [
    "benchmark/gold_programs/dkpes_model_development_1.py",
    "benchmark/eval_programs/eval_dkpes_model_development_1.py",
    "benchmark/eval_programs/dkpes_model_eval.py",
    "benchmark/scoring_rubrics/dkpes_model_development_1_rubric.json",
]
for f in files:
    p = Path(f)
    print("\n" + "="*80)
    print(f, "exists:", p.exists())
    if p.exists():
        txt = p.read_text(errors="ignore")
        if f.endswith(".json"):
            try:
                print(json.dumps(json.loads(txt), indent=2)[:8000])
            except Exception:
                print(txt[:8000])
        else:
            print(txt[:12000])

gold = Path("benchmark/eval_programs/gold_results/dkpes_test_gold.csv")
print("\n" + "="*80)
print("Gold result exists:", gold.exists())
if gold.exists():
    print(gold.read_text(errors="ignore")[:4000])