import os
from pathlib import Path

search_roots = [Path("benchmark"), Path(".")]
terms = ["mist_hr", "hr_sample_mist", "MIST3", "baseline_hr", "onset_hr", "cft", "cold face"]
for base in search_roots:
    print(f"\nText searching under {base} exists={base.exists()}")
    if not base.exists():
        continue
    nfiles = 0
    hits = 0
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
        for f in files:
            path = Path(root) / f
            if path.suffix.lower() not in {".py", ".txt", ".md", ".json", ".yaml", ".yml", ".csv"}:
                continue
            nfiles += 1
            try:
                text = path.read_text(errors="ignore")
            except Exception:
                continue
            low = text.lower()
            matched = [t for t in terms if t.lower() in low]
            if matched:
                hits += 1
                print("HIT", path, "terms", matched)
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if any(t.lower() in line.lower() for t in terms):
                        print(f"  L{i+1}: {line[:300]}")
    print("Scanned text files:", nfiles, "hits:", hits)