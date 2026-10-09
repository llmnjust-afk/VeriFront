"""AUROC with explicit NA handling (Prompt_V2 §5.3).

Rules implemented here:
- a checker's AUROC is a property of a LABELED SAMPLE, never of one output;
- if either class is empty, we return auroc=None with an explicit reason —
  "no estimable AUROC" must NOT be disguised as the number 0;
- perfect separation is allowed but flagged, because it usually means the
  sample is too easy or contaminated.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence, Tuple


def _average_ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # 1-based average rank for ties
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def auroc(scores: Sequence[float], labels: Sequence[int]) -> Optional[float]:
    """Mann-Whitney AUROC. labels: 1=correct/positive, 0=incorrect/negative."""
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have equal length")
    pos = [float(s) for s, l in zip(scores, labels) if int(l) == 1]
    neg = [float(s) for s, l in zip(scores, labels) if int(l) == 0]
    if not pos or not neg:
        return None
    allv = pos + neg
    ranks = _average_ranks(allv)
    n1, n0 = len(pos), len(neg)
    sum_pos = sum(ranks[:n1])
    u = sum_pos - n1 * (n1 + 1) / 2.0
    return u / (n1 * n0)


def compute_auroc_or_na(samples: Sequence[Tuple[float, int]]) -> Dict[str, object]:
    """samples: [(checker_score, correctness_label 0/1)]. Returns a dict that
    always states whether the estimate is usable."""
    scores = [s for s, _ in samples]
    labels = [l for _, l in samples]
    n_pos = sum(1 for l in labels if int(l) == 1)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return {
            "auroc": None,
            "usable": False,
            "reason": f"missing_class (pos={n_pos}, neg={n_neg}) — report coverage, not a fake AUROC",
            "n_samples": len(labels),
        }
    value = auroc(scores, labels)
    separable = value in (0.0, 1.0)
    return {
        "auroc": value,
        "usable": True,
        "separable_flag": separable,
        "n_samples": len(labels),
        "n_pos": n_pos,
        "n_neg": n_neg,
    }


def bootstrap_ci(
    samples: Sequence[Tuple[float, int]],
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Percentile bootstrap over labeled samples. Resamples that lose a class
    are skipped and counted (reported, not hidden)."""
    rng = random.Random(seed)
    n = len(samples)
    if n == 0:
        return {"lo": None, "hi": None, "skipped": 0}
    stats: List[float] = []
    skipped = 0
    base = compute_auroc_or_na(samples)
    if not base["usable"]:
        return {"lo": None, "hi": None, "skipped": 0, "reason": base["reason"]}
    for _ in range(n_boot):
        draw = [samples[rng.randrange(n)] for _ in range(n)]
        v = auroc([s for s, _ in draw], [l for _, l in draw])
        if v is None:
            skipped += 1
            continue
        stats.append(v)
    if not stats:
        return {"lo": None, "hi": None, "skipped": skipped}
    stats.sort()

    def pct(p: float) -> float:
        idx = min(len(stats) - 1, max(0, int(round(p * (len(stats) - 1)))))
        return stats[idx]

    return {"lo": pct(alpha / 2), "hi": pct(1 - alpha / 2), "skipped": skipped, "n_boot": n_boot}
