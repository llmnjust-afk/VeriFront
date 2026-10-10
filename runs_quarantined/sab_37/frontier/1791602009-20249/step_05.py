import os, json, pkgutil, inspect
from pathlib import Path
import pandas as pd
import numpy as np

# Re-inspect BioPsyKit CFT-related APIs with concise output
try:
    import biopsykit
    print("biopsykit version:", getattr(biopsykit, "__version__", "unknown"), "file:", biopsykit.__file__)
    cft_mods = []
    for importer, modname, ispkg in pkgutil.walk_packages(biopsykit.__path__, biopsykit.__name__ + "."):
        low = modname.lower()
        if "cft" in low or "cold" in low or "mist" in low:
            cft_mods.append(modname)
    print("CFT-like modules:", cft_mods)
    for modname in cft_mods:
        try:
            mod = __import__(modname, fromlist=["*"])
            print("\nMODULE", modname, "file", getattr(mod, "__file__", None))
            names = [n for n in dir(mod) if not n.startswith("_")]
            print("public names:", names[:100])
            for n in names:
                obj = getattr(mod, n)
                if inspect.isclass(obj) or inspect.isfunction(obj):
                    print("OBJ", n, "type", type(obj))
                    try:
                        print(" signature:", inspect.signature(obj))
                    except Exception as e:
                        print(" signature err:", e)
                    doc = inspect.getdoc(obj)
                    if doc:
                        print(" doc:", doc[:800].replace("\n", " | "))
        except Exception as e:
            print(" import module failed", modname, repr(e))
except Exception as e:
    print("biopsykit import failed:", repr(e))

# Search installed biopsykit source for key strings
try:
    import biopsykit
    base = Path(biopsykit.__file__).parent
    print("\nSearching source in", base)
    for term in ["baseline_hr", "onset_hr", "onset_hr_percent", "Cold Face", "cold face", "cft"]:
        hits = []
        for py in base.rglob("*.py"):
            try:
                txt = py.read_text(errors="ignore")
            except Exception:
                continue
            if term in txt:
                hits.append(str(py.relative_to(base)))
        print("term", repr(term), "hits", hits[:30], "count", len(hits))
except Exception as e:
    print("source search failed", repr(e))