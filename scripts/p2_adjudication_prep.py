#!/usr/bin/env python3
"""Build the adjudication pack for >1-level A/B disagreements (codebook v1.3 sec2:
differences >1 level require discussion -> consensus; <=1 level auto-mean)."""
import csv
from collections import defaultdict

A = 'reports/annotation/p2_blind_draft_annotatorA.csv'
B = 'reports/annotation/p2_blind_filled_annotatorB.csv'
OUT = 'reports/annotation/p2_adjudication_pack.md'


def load(p):
    return {r['point_id']: r for r in csv.DictReader(open(p))}


def main():
    a, b = load(A), load(B)
    dims = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']
    groups = defaultdict(list)
    for p in sorted(a):
        for d in dims:
            x, y = a[p][d], b[p][d]
            if x and y and abs(int(x) - int(y)) >= 2:
                groups[d].append(p)
    L = ["# P2 sec4.2 adjudication pack (>1-level disagreements)", "",
         "Rule (codebook v1.3 sec2): >1-level differences require discussion -> consensus value.",
         "Each item lists both sides' rationales verbatim; the adjudicator assigns the final value.",
         ""]
    for d in ['F1', 'F5', 'F6']:
        if d not in groups:
            continue
        L.append(f"## {d}: {len(groups[d])} points")
        for p in groups[d]:
            L.append(f"### {p}  (A={a[p][d]}, B={b[p][d]})")
            L.append(f"- A rationale: {a[p]['rationale']}")
            L.append(f"- B rationale: {b[p]['rationale']}")
            L.append(f"- FINAL ({d}) = ____")
            L.append("")
    # 1-level summary table for the auto-mean record
    L.append("## Auto-mean items (|diff| = 1, no discussion per frozen rule)")
    for p in sorted(a):
        for d in dims:
            x, y = a[p][d], b[p][d]
            if x and y and abs(int(x) - int(y)) == 1:
                L.append(f"- {p} {d}: A={x} B={y} -> {(int(x)+int(y))/2:g}")
    open(OUT, 'w').write("\n".join(L) + "\n")
    print("wrote", OUT, "| groups:", {d: len(v) for d, v in groups.items()})


if __name__ == '__main__':
    main()
