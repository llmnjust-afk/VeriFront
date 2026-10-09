"""Pre-registered stratified sampling of replacement points (Prompt_V2 §6.3).

Rules enforced by design:
- only anchors whose recovery has been verified (recoverable=True) are eligible;
- stratification keys and the RNG seed are recorded into a config artifact that
  must be written to reports/pilot/sampling_config.json BEFORE execution;
- every excluded candidate carries an explicit reason; exclusions are returned,
  never silently dropped.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class ReplacementCandidate:
    task_id: str
    trajectory_id: str
    step_id: str
    position: int                  # 0-based index of the step within its trajectory
    n_actions_in_trajectory: int   # used for position bucketing
    step_type: str                 # eight-type taxonomy or 'unassignable'
    recoverable: bool = True
    exclude_reason: Optional[str] = None


def position_bucket(candidate: ReplacementCandidate) -> str:
    n = max(1, candidate.n_actions_in_trajectory)
    r = candidate.position / n
    if r < 1 / 3:
        return "early"
    if r < 2 / 3:
        return "mid"
    return "late"


def sample_replacement_points(
    candidates: Sequence[ReplacementCandidate],
    n: int,
    seed: int = 0,
    stratify_by: Sequence[str] = ("step_type",),
) -> Tuple[List[ReplacementCandidate], List[Tuple[ReplacementCandidate, str]], Dict[str, Any]]:
    """Returns (selected, excluded_with_reasons, pre_registration_record)."""
    if n <= 0:
        raise ValueError("n must be positive")

    eligible: List[ReplacementCandidate] = []
    excluded: List[Tuple[ReplacementCandidate, str]] = []
    for c in candidates:
        if c.recoverable and not c.exclude_reason:
            eligible.append(c)
        else:
            excluded.append((c, c.exclude_reason or "not_recoverable"))

    rng = random.Random(seed)
    key_funcs = {
        "step_type": lambda c: c.step_type,
        "position": lambda c: position_bucket(c),
        "task": lambda c: c.task_id,
    }
    for k in stratify_by:
        if k not in key_funcs:
            raise ValueError(f"unknown stratification key {k!r}")

    def strat_key(c: ReplacementCandidate) -> Tuple:
        return tuple(key_funcs[k](c) for k in stratify_by)

    strata: Dict[Tuple, List[ReplacementCandidate]] = {}
    for c in sorted(eligible, key=lambda x: (x.task_id, x.trajectory_id, x.step_id)):
        strata.setdefault(strat_key(c), []).append(c)

    # proportional allocation with largest-remainder rounding
    total = len(eligible)
    quotas: Dict[Tuple, int] = {}
    raw = {s: len(members) * n / total for s, members in strata.items()}
    floors = {s: int(v) for s, v in raw.items()}
    remainder = n - sum(floors.values())
    order = sorted(strata, key=lambda s: (-(raw[s] - floors[s]), s))
    for s in order[:remainder]:
        floors[s] += 1
    quotas = {s: min(floors[s], len(strata[s])) for s in strata}

    selected: List[ReplacementCandidate] = []
    for s in sorted(strata):
        members = strata[s]
        take = quotas[s]
        if take >= len(members):
            selected.extend(members)
        else:
            selected.extend(rng.sample(members, take))

    # if strata were exhausted, fill the remainder from the leftover pool
    if len(selected) < n:
        chosen_ids = {id(c) for c in selected}
        leftover = [c for c in eligible if id(c) not in chosen_ids]
        selected.extend(rng.sample(leftover, min(n - len(selected), len(leftover))))

    record: Dict[str, Any] = {
        "seed": seed,
        "n_requested": n,
        "stratify_by": list(stratify_by),
        "eligible_count": len(eligible),
        "excluded_count": len(excluded),
        "strata_eligible": {repr(s): len(m) for s, m in sorted(strata.items(), key=lambda kv: repr(kv[0]))},
        "selected_count": len(selected),
        "candidates": [asdict(c) for c in sorted(selected, key=lambda x: (x.task_id, x.step_id))],
        "excluded": [
            {**asdict(c), "reason": reason} for c, reason in excluded
        ],
    }
    return selected, excluded, record
