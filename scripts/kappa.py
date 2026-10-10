"""Cohen's kappa between two annotators over the trial step set.

  python scripts/kappa.py --a reports/annotation/annotatorA.jsonl \
      --b reports/annotation/annotatorB.jsonl

Computes unweighted kappa for step_type and role_in_outcome (neutral vs
critical_* merged for a stricter-but-stabler second metric).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def kappa(a: list, b: list) -> float:
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    args = ap.parse_args()

    A = {json.loads(l)["i"]: json.loads(l) for l in open(args.a, encoding="utf-8") if l.strip()}
    B = {json.loads(l)["i"]: json.loads(l) for l in open(args.b, encoding="utf-8") if l.strip()}
    common = sorted(set(A) & set(B))
    if len(common) < len(A):
        print(f"WARNING: B missing {len(A) - len(common)} steps: {sorted(set(A) - set(B))[:10]}")

    ta = [A[i]["step_type"] for i in common]
    tb = [B[i]["step_type"] for i in common]
    ra = ["critical" if str(A[i]["role_in_outcome"]).startswith("critical") else "neutral"
          for i in common]
    rb = ["critical" if str(B[i]["role_in_outcome"]).startswith("critical") else "neutral"
          for i in common]
    ra_full = [A[i]["role_in_outcome"] for i in common]
    rb_full = [B[i]["role_in_outcome"] for i in common]

    print(f"n={len(common)}")
    print(f"step_type kappa:      {kappa(ta, tb):+.3f}")
    print(f"role (3-way) kappa:   {kappa(ra_full, rb_full):+.3f}")
    print(f"role (crit/neutral):  {kappa(ra, rb):+.3f}")
    disagree_type = [(i, A[i]['step_type'], B[i]['step_type']) for i in common if A[i]["step_type"] != B[i]["step_type"]]
    print(f"type disagreements: {len(disagree_type)}")
    for i, x, y in disagree_type[:15]:
        print(f"  step {i}: A={x} B={y}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
