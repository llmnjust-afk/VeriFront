#!/usr/bin/env python3
from pathlib import Path
import inspect
import importlib
import pkgutil

import biopsykit.signals.ecg as ecg

print("biopsykit.signals.ecg module:", ecg)
print("Attributes:")
for name in dir(ecg):
    if not name.startswith("_"):
        attr = getattr(ecg, name)
        print(" ", name, type(attr))

print("\nSubmodules under biopsykit.signals.ecg:")
for m in pkgutil.iter_modules(ecg.__path__, ecg.__name__ + "."):
    print(" ", m.name, "pkg" if m.ispkg else "mod")
    try:
        mod = importlib.import_module(m.name)
        public = [n for n in dir(mod) if not n.startswith("_")]
        print("    public:", public[:80])
        for n in public:
            if any(s in n.lower() for s in ["peak", "outlier", "rpe", "r_peak", "qrs", "detect", "correct"]):
                obj = getattr(mod, n)
                print("    candidate:", n, type(obj))
                try:
                    print("      sig:", inspect.signature(obj))
                except Exception as e:
                    pass
    except Exception as e:
        print("    import error:", repr(e))

# Also recursively search one level deeper
print("\nRecursive candidate search:")
for finder, name, ispkg in pkgutil.walk_packages(ecg.__path__, ecg.__name__ + "."):
    if name.count(".") > 5:
        continue
    try:
        mod = importlib.import_module(name)
    except Exception as e:
        print(" import fail", name, repr(e))
        continue
    candidates = []
    for n in dir(mod):
        if not n.startswith("_") and any(s in n.lower() for s in ["peak", "outlier", "rpe", "qrs", "detect", "correct"]):
            candidates.append(n)
    if candidates:
        print(" ", name, candidates)
        for n in candidates[:20]:
            obj = getattr(mod, n)
            try:
                sig = inspect.signature(obj)
                print("    ", n, sig)
            except Exception:
                print("    ", n, type(obj))