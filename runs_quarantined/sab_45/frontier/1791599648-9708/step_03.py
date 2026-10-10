#!/usr/bin/env python3
import os, glob, inspect, pkgutil, importlib
import pandas as pd

# Prefer the dataset in this run's benchmark folder.
candidates = [
    "benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl",
    "biopsykit_questionnaire_data/questionnaire_data.pkl",
]
path = next((p for p in candidates if os.path.exists(p)), None)
if path is None:
    matches = sorted(glob.glob("/data/lab/VeriFront/runs/sab_45/frontier/1791599648-9708/benchmark/datasets/biopsykit_questionnaire_data/questionnaire_data.pkl"))
    if not matches:
        matches = sorted(glob.glob("/data/**/biopsykit_questionnaire_data/questionnaire_data.pkl", recursive=True))
    path = matches[0]
print("Using dataset:", path)

df = pd.read_pickle(path)
print("Loaded shape:", df.shape)
print("Index name:", df.index.name, "Index values:", df.index.tolist())
print("Columns first:", list(df.columns)[:12])
pss_cols = [f"PSS_{i:02d}" for i in range(1, 11)]
print("PSS head with index:")
print(df[pss_cols].head(13).to_string())

# Manual candidate scores
negative_items = ["PSS_01", "PSS_02", "PSS_03", "PSS_06", "PSS_09", "PSS_10"]
positive_items = ["PSS_04", "PSS_05", "PSS_07", "PSS_08"]
manual = pd.DataFrame(index=df.index)
manual["helpless_raw"] = df[negative_items].sum(axis=1)
manual["selfeff_raw"] = df[positive_items].sum(axis=1)
manual["selfeff_reversed"] = (4 - df[positive_items]).sum(axis=1)
manual["total"] = manual["helpless_raw"] + manual["selfeff_reversed"]
print("Manual candidate scores:")
print(manual.to_string())

# Inspect BioPsyKit if present
try:
    import biopsykit
    print("biopsykit version:", getattr(biopsykit, "__version__", "unknown"))
    names = []
    for modinfo in pkgutil.walk_packages(biopsykit.__path__, biopsykit.__name__ + "."):
        if "question" in modinfo.name.lower() or "pss" in modinfo.name.lower():
            names.append(modinfo.name)
    print("Potential modules:", names[:100])
    for modname in names[:50]:
        try:
            mod = importlib.import_module(modname)
            attrs = [a for a in dir(mod) if "PSS" in a or "Pss" in a or "pss" in a or "Question" in a]
            if attrs:
                print("Module", modname, "attrs", attrs[:50])
                for a in attrs[:10]:
                    obj = getattr(mod, a)
                    try:
                        print(" ", a, "=", obj, "sig", inspect.signature(obj) if callable(obj) else "")
                    except Exception:
                        print(" ", a, "=", obj)
        except Exception as e:
            pass
except Exception as e:
    print("BioPsyKit unavailable/error:", repr(e))