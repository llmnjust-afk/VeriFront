import os

path = "benchmark/gold_programs/CogSci_pattern_high_sim.py"
print("Reading", path)
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    txt = f.read()
print(txt)

eval_path = "benchmark/eval_programs/CogSci_pattern_high_sim_eval.py"
print("\nReading", eval_path)
with open(eval_path, "r", encoding="utf-8", errors="ignore") as f:
    print(f.read())