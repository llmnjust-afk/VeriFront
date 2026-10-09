"""Checker protocol and registry with availability/coverage tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class CheckerResult:
    checker_name: str
    passed: Optional[bool]          # None = could not evaluate
    score: Optional[float] = None   # continuous risk/quality score if the checker provides one
    details: Dict[str, Any] = field(default_factory=dict)
    cost_seconds: float = 0.0
    extra_model_calls: int = 0      # deterministic checkers are 0; "low cost" must be measured


Checker = Any  # duck-typed: check(output, context=None) -> CheckerResult


class CheckerRegistry:
    def __init__(self) -> None:
        self._by_type: Dict[str, List[Checker]] = {}

    def register(self, step_type: str, checker: Checker) -> None:
        self._by_type.setdefault(step_type, []).append(checker)

    def available_for(self, step_type: str) -> List[Checker]:
        return list(self._by_type.get(step_type, []))

    def coverage_map(self, step_types: Optional[List[str]] = None) -> Dict[str, int]:
        types = step_types if step_types is not None else sorted(self._by_type)
        return {t: len(self._by_type.get(t, [])) for t in types}

    def run_all(self, step_type: str, output: Any, context: Optional[Dict] = None) -> List[CheckerResult]:
        results = []
        for checker in self.available_for(step_type):
            t0 = time.monotonic()
            res = checker.check(output, context)
            res.cost_seconds = time.monotonic() - t0
            results.append(res)
        return results


def timed(fn: Callable) -> Callable:
    """Decorator that fills CheckerResult.cost_seconds is NOT used automatically;
    the registry measures wall time around check() instead. Kept for future use."""

    def wrapper(*args, **kwargs):
        t0 = time.monotonic()
        out = fn(*args, **kwargs)
        elapsed = time.monotonic() - t0
        if hasattr(out, "cost_seconds"):
            out.cost_seconds = elapsed
        return out

    return wrapper
