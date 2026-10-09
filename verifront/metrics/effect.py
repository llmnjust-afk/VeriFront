"""ΔSR with task-level clustering (Prompt_V2 §8.2).

The task is the unit of analysis: steps/trajectories within one task are NOT
independent. Point estimate weights tasks equally; the bootstrap resamples
TASKS, not step instances.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Dict, List, Sequence


def _mean(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("mean of empty sequence")
    return sum(xs) / len(xs)


def delta_sr(records: Sequence[Dict]) -> Dict[str, Any]:  # noqa: F811 - annotation fix
    """records: [{"task_id", "arm" in {"control","treatment"}, "success": bool}].
    control arm = frontier resampling at the same pre-state;
    treatment arm = local model generates the step.
    Returns per-task deltas + point estimate + exclusions."""
    by_task: Dict[str, Dict[str, List[bool]]] = defaultdict(lambda: {"control": [], "treatment": []})
    n_instances = 0
    for r in records:
        arm = r["arm"]
        if arm not in ("control", "treatment"):
            raise ValueError(f"unknown arm {arm!r}")
        if r.get("success") is None:
            continue  # unevaluated runs are excluded, caller must report counts
        by_task[str(r["task_id"])][arm].append(bool(r["success"]))
        n_instances += 1

    deltas: List[float] = []
    excluded: List[str] = []
    for tid in sorted(by_task):
        c, t = by_task[tid]["control"], by_task[tid]["treatment"]
        if not c or not t:
            excluded.append(tid)
            continue
        deltas.append(_mean(c) - _mean(t))

    estimate = _mean(deltas) if deltas else None
    return {
        "delta_sr": estimate,
        "task_deltas": deltas,
        "n_tasks_used": len(deltas),
        "n_tasks_excluded": len(excluded),
        "excluded_task_ids": excluded,
        "n_instances": n_instances,
    }


def cluster_bootstrap_ci(
    task_deltas: Sequence[float],
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """Percentile CI by resampling tasks with replacement."""
    rng = random.Random(seed)
    n = len(task_deltas)
    if n == 0:
        return {"lo": None, "hi": None, "n_boot": n_boot}
    stats: List[float] = []
    for _ in range(n_boot):
        draw = [task_deltas[rng.randrange(n)] for _ in range(n)]
        stats.append(sum(draw) / n)
    stats.sort()

    def pct(p: float) -> float:
        idx = min(len(stats) - 1, max(0, int(round(p * (len(stats) - 1)))))
        return stats[idx]

    return {"lo": pct(alpha / 2), "hi": pct(1 - alpha / 2), "n_boot": n_boot, "n_tasks": n}


def summarize(records: Sequence[Dict], seed: int = 0, n_boot: int = 2000) -> Dict[str, Any]:
    d = delta_sr(records)
    ci = cluster_bootstrap_ci(list(d["task_deltas"]), n_boot=n_boot, seed=seed)
    return {**d, "ci95": {"lo": ci["lo"], "hi": ci["hi"]}, "note": "task-clustered bootstrap; wide intervals at pilot n are expected and must be reported as such"}
