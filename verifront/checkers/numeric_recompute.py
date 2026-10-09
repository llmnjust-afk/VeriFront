"""Independent numeric recomputation checks."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, Optional


class NumericRecomputeChecker:
    """Recompute expected values from `output["inputs"]` via an INDEPENDENT
    implementation and compare against the output's claimed values.

    Caveat inherited from the protocol: if the recompute shares the same method
    or input error as the candidate, both can agree on a wrong value — recorded
    in details as an assumption, not a guarantee.
    """

    def __init__(
        self,
        name: str,
        recompute: Callable[[Dict], Dict],
        fields: list,
        rtol: float = 1e-6,
        atol: float = 0.0,
    ):
        self.name = name
        self.recompute = recompute
        self.fields = list(fields)
        self.rtol = rtol
        self.atol = atol

    def check(self, output: Any, context: Optional[Dict] = None):
        from .base import CheckerResult

        if not isinstance(output, dict):
            return CheckerResult(self.name, passed=False, details={"problems": ["output is not a dict"]})
        try:
            expected = self.recompute(output.get("inputs") or {})
        except Exception as e:  # noqa: BLE001
            return CheckerResult(self.name, passed=False, details={"problems": [f"recompute raised: {type(e).__name__}: {e}"]})
        problems = []
        for f in self.fields:
            if f not in output:
                problems.append(f"missing claimed field: {f}")
                continue
            if f not in expected:
                problems.append(f"recompute did not produce: {f}")
                continue
            got, exp = output[f], expected[f]
            ok = False
            try:
                ok = math.isclose(float(got), float(exp), rel_tol=self.rtol, abs_tol=self.atol)
            except (TypeError, ValueError):
                ok = got == exp
            if not ok:
                problems.append(f"value mismatch for {f}: claimed {got!r}, recomputed {exp!r}")
        return CheckerResult(self.name, passed=not problems, details={"problems": problems})
