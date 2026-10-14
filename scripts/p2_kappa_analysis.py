#!/usr/bin/env python3
"""P2 sec4.2 inter-annotator agreement: A (blind draft) vs B (filled template).

- F1-F6: weighted Cohen's kappa (quadratic) over points where BOTH annotators
  gave a value; blanks are excluded pairwise and reported.
- F7: unweighted kappa + raw agreement (F7 is nominal; codebook v1.3 sec2).
- No replacement-experiment data is read (blinding preserved).

Usage: python3 scripts/p2_kappa_analysis.py
Output: reports/annotation/p2_kappa_report.md
"""
import csv

A = 'reports/annotation/p2_blind_draft_annotatorA.csv'
B = 'reports/annotation/p2_blind_filled_annotatorB.csv'
OUT = 'reports/annotation/p2_kappa_report.md'


def kappa_weighted(xs, ys, levels=(0, 1, 2)):
    """Quadratic-weighted Cohen's kappa for ordinal levels (no deps)."""
    k = len(levels)
    idx = {v: i for i, v in enumerate(levels)}
    n = len(xs)
    O = [[0.0] * k for _ in range(k)]
    for x, y in zip(xs, ys):
        O[idx[x]][idx[y]] += 1
    O = [[c / n for c in row] for row in O]
    ra = [sum(O[i]) for i in range(k)]
    rb = [sum(O[i][j] for i in range(k)) for j in range(k)]
    W = [[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    num = sum(W[i][j] * O[i][j] for i in range(k) for j in range(k))
    den = sum(W[i][j] * ra[i] * rb[j] for i in range(k) for j in range(k))
    return 1.0 if den == 0 else 1 - num / den


def kappa_unweighted(xs, ys):
    n = len(xs)
    po = sum(1 for x, y in zip(xs, ys) if x == y) / n
    ca, cb = {}, {}
    for x in xs:
        ca[x] = ca.get(x, 0) + 1
    for y in ys:
        cb[y] = cb.get(y, 0) + 1
    pe = sum(ca[kk] * cb.get(kk, 0) for kk in ca) / (n * n)
    return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)


def load(path):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rows[r['point_id']] = r
    return rows


def fmtk(k, n, po):
    tag = 'OK' if k >= 0.6 else 'LOW (<0.6 -> clarify & re-annotate)'
    return f"{k:+.3f} (n={n}, raw agreement {po:.3f}) {tag}"


def main():
    a, b = load(A), load(B)
    assert set(a) == set(b) and len(a) == 38
    L = ["# P2 sec4.2 A/B inter-annotator agreement (pre-adjudication)", "",
         "Blinding note: F2 has 2 B-side blanks (kept after definition",
         "clarification); those points are excluded from F2 pairwise kappa.", ""]
    dims = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']
    low = []
    for d in dims:
        pairs = [(a[p][d], b[p][d]) for p in a if a[p][d] != '' and b[p][d] != '']
        xs, ys = zip(*pairs)
        n_blank = sum(1 for p in a if a[p][d] == '' or b[p][d] == '')
        k = kappa_weighted(xs, ys, levels=('0', '1', '2'))
        po = sum(1 for x, y in pairs if x == y) / len(pairs)
        L.append(f"## {d} (weighted kappa, quadratic)")
        L.append(f"- kappa = {fmtk(k, len(pairs), po)}")
        L.append(f"- A dist: {dict(sorted((str(x), xs.count(x)) for x in set(xs)))}"
                 f" | B dist: {dict(sorted((str(y), ys.count(y)) for y in set(ys)))}")
        L.append(f"- blanks excluded: {n_blank}")
        if k < 0.6:
            low.append(d)
        L.append("- disagreements:")
        for p in sorted(a):
            x, y = a[p][d], b[p][d]
            if x != '' and y != '' and x != y:
                L.append(f"  - {p}: A={x} B={y} | A-rat: {a[p]['rationale'][:60]}"
                         f" | B-rat: {b[p]['rationale'][:60]}")
        L.append("")
    # F7 nominal
    xs = [a[p]['F7'] for p in a]
    ys = [b[p]['F7'] for p in a]
    k7 = kappa_unweighted(xs, ys)
    po7 = sum(1 for x, y in zip(xs, ys) if x == y) / len(xs)
    L.append("## F7 (unweighted kappa, nominal)")
    L.append(f"- kappa = {fmtk(k7, len(xs), po7)}")
    L.append(f"- A dist: {dict(sorted((x, xs.count(x)) for x in set(xs)))}"
             f" | B dist: {dict(sorted((y, ys.count(y)) for y in set(ys)))}")
    L.append("")
    L.append("## Dimensions below 0.6 (require clarification + re-annotation per codebook sec2)")
    L.append("- " + (", ".join(low) if low else "none"))
    L.append("")
    L.append("## B-side blanks (final, kept after clarification)")
    for p in sorted(a):
        for d in dims:
            if b[p][d] == '':
                L.append(f"- {p} {d}=blank | B rationale: {b[p]['rationale']}")
    open(OUT, 'w').write("\n".join(L) + "\n")
    print("wrote", OUT, "| low-kappa dims:", low or "none")


if __name__ == '__main__':
    main()
