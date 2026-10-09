"""Schema / type / range checks for structured step outputs."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


class SchemaChecker:
    """required: {key: (types...)}; ranges: {key: (min, max)}; allowed: {key: set}."""

    def __init__(
        self,
        name: str = "schema",
        required: Optional[Dict[str, Tuple[type, ...]]] = None,
        ranges: Optional[Dict[str, Tuple[float, float]]] = None,
        allowed: Optional[Dict[str, set]] = None,
    ):
        self.name = name
        self.required = required or {}
        self.ranges = ranges or {}
        self.allowed = allowed or {}

    def check(self, output: Any, context: Optional[Dict] = None):
        from .base import CheckerResult

        problems = []
        if not isinstance(output, dict):
            return CheckerResult(self.name, passed=False, details={"problems": ["output is not a dict"]})
        for key, types in self.required.items():
            if key not in output:
                problems.append(f"missing key: {key}")
            elif not isinstance(output[key], types):
                problems.append(f"wrong type for {key}: got {type(output[key]).__name__}, want {[t.__name__ for t in types]}")
        for key, (lo, hi) in self.ranges.items():
            if key in output and isinstance(output[key], (int, float)):
                v = output[key]
                if not (lo <= v <= hi):
                    problems.append(f"out of range for {key}: {v} not in [{lo}, {hi}]")
        for key, vals in self.allowed.items():
            if key in output and output[key] not in vals:
                problems.append(f"disallowed value for {key}: {output[key]!r}")
        return CheckerResult(self.name, passed=not problems, details={"problems": problems})
