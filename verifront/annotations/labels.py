"""Labels for step type and step correctness (kept strictly separate).

Type label answers "what is this step doing?"; correctness label answers "is
this step's output correct for the current scientific goal?" — with evidence.
Blinding rule: annotators must not see model identity, final task success, or
checker scores (Prompt_V2 §5.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .. import UNASSIGNABLE

CORRECTNESS_VALUES = {"correct", "incorrect", "uncertain"}


@dataclass
class LabelRecord:
    instance_id: str
    step_type: str                     # one of the 8 types or 'unassignable'
    correctness: Optional[str] = None  # correct / incorrect / uncertain / None (not assessed)
    evidence: str = ""
    annotator: str = ""
    blinded: bool = True

    def validate(self) -> List[str]:
        errs = []
        if not self.instance_id:
            errs.append("missing instance_id")
        if not self.step_type:
            errs.append("missing step_type")
        if self.correctness is not None and self.correctness not in CORRECTNESS_VALUES:
            errs.append(f"invalid correctness {self.correctness!r}")
        if self.correctness in {"correct", "incorrect"} and not self.evidence.strip():
            errs.append("correctness verdict requires evidence")
        return errs


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> Optional[float]:
    """Cohen's kappa for categorical labels. Returns None for degenerate cases
    (empty input or single-category marginals), so callers cannot mistake a
    degenerate agreement for kappa=1."""
    if len(labels_a) != len(labels_b):
        raise ValueError("label sequences must have equal length")
    n = len(labels_a)
    if n == 0:
        return None
    cats = sorted(set(labels_a) | set(labels_b))
    joint: Dict[Tuple[str, str], int] = {(x, y): 0 for x in cats for y in cats}
    for x, y in zip(labels_a, labels_b):
        joint[(x, y)] += 1
    po = sum(joint[(c, c)] for c in cats) / n
    row_marg = {c: sum(joint[(c, y)] for y in cats) / n for c in cats}
    col_marg = {c: sum(joint[(x, c)] for x in cats) / n for c in cats}
    pe = sum(row_marg[c] * col_marg[c] for c in cats)
    if pe >= 1.0:
        return None
    return (po - pe) / (1.0 - pe)


def confusion_matrix(
    labels_a: Sequence[str], labels_b: Sequence[str]
) -> Dict[Tuple[str, str], int]:
    if len(labels_a) != len(labels_b):
        raise ValueError("label sequences must have equal length")
    counts: Dict[Tuple[str, str], int] = {}
    for x, y in zip(labels_a, labels_b):
        counts[(x, y)] = counts.get((x, y), 0) + 1
    return counts


def merge_double_annotation(
    recs_a: Dict[str, LabelRecord],
    recs_b: Dict[str, LabelRecord],
    value: str = "step_type",
) -> Dict[str, str]:
    """Merge two annotators' labels per instance.
    agree -> that value; disagree -> 'needs_arbitration'; missing -> 'missing'."""
    out: Dict[str, str] = {}
    for iid in sorted(set(recs_a) | set(recs_b)):
        a, b = recs_a.get(iid), recs_b.get(iid)
        va = getattr(a, value) if a else None
        vb = getattr(b, value) if b else None
        if va is None or vb is None:
            out[iid] = "missing"
        elif va == vb:
            out[iid] = va
        else:
            out[iid] = "needs_arbitration"
    return out
