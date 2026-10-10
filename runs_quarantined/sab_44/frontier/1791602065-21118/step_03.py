#!/usr/bin/env python3
import os
from pathlib import Path
import pkgutil, importlib, inspect

print("Recursive listing to depth 4:")
def list_tree(path=Path("."), prefix="", depth=0, maxdepth=4):
    if depth > maxdepth:
        return
    try:
        entries = sorted(path.iterdir())
    except Exception as e:
        print(prefix, "ERR", e)
        return
    for p in entries:
        info = "dir" if p.is_dir() else f"file {p.stat().st_size}"
        print(f"{prefix}{p.name} ({info})")
        if p.is_dir() and depth < maxdepth and p.name not in {"__pycache__", ".git"}:
            list_tree(p, prefix + "  ", depth+1, maxdepth)
list_tree()

print("\nSearching for pkl/csv/parquet files under current tree:")
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
    for f in files:
        if f.lower().endswith((".pkl",".pickle",".csv",".parquet",".json")):
            p = Path(root)/f
            print(p, p.stat().st_size)

print("\nInspect predict_pipeline_acceleration signature/source excerpt")
try:
    from biopsykit.sleep import sleep_processing_pipeline
    print("module", sleep_processing_pipeline, sleep_processing_pipeline.__file__)
    fun = sleep_processing_pipeline.predict_pipeline_acceleration
    print("signature:", inspect.signature(fun))
    src = inspect.getsource(fun)
    print(src[:4000])
except Exception as e:
    print("ERROR:", repr(e))
    import traceback; traceback.print_exc()