"""Cost accounting that includes FULL continuation, not just the replaced step.

(Prompt_V2 §9.2: the original plan's biggest budget-underestimation risk.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Price:
    model_id: str
    prompt_usd_per_1m: float
    completion_usd_per_1m: float


def cost_of(prompt_tokens: int, completion_tokens: int, price: Price) -> float:
    return (prompt_tokens * price.prompt_usd_per_1m + completion_tokens * price.completion_usd_per_1m) / 1_000_000.0


def total_cost(rows: Iterable[Dict], prices: Dict[str, Price]) -> Dict[str, object]:
    """rows: [{"model_id", "prompt_tokens", "completion_tokens", "phase",
    "instance_id"}] — every continuation, retry, failed run and eval rerun must
    appear as a row (phase in {"initial","replacement_step","continuation","eval","debug"})."""
    per_model: Dict[str, Dict[str, float]] = {}
    per_phase: Dict[str, float] = {}
    unknown_models: List[str] = []
    n_rows = 0
    for r in rows:
        n_rows += 1
        mid = str(r["model_id"])
        price = prices.get(mid)
        if price is None:
            unknown_models.append(mid)
            continue
        c = cost_of(int(r.get("prompt_tokens", 0)), int(r.get("completion_tokens", 0)), price)
        m = per_model.setdefault(mid, {"prompt_tokens": 0.0, "completion_tokens": 0.0, "usd": 0.0})
        m["prompt_tokens"] += int(r.get("prompt_tokens", 0))
        m["completion_tokens"] += int(r.get("completion_tokens", 0))
        m["usd"] += c
        per_phase[r.get("phase", "unspecified")] = per_phase.get(r.get("phase", "unspecified"), 0.0) + c
    total = sum(m["usd"] for m in per_model.values())
    return {
        "n_rows": n_rows,
        "per_model": per_model,
        "per_phase": per_phase,
        "total_usd": total,
        "unknown_models": sorted(set(unknown_models)),
    }


def per_instance_cost(total_usd: float, n_instances: int) -> Tuple[float, str]:
    if n_instances <= 0:
        return float("nan"), "n_instances must be positive"
    return total_usd / n_instances, "includes full continuation and overhead rows"
