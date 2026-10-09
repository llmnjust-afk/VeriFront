"""Deterministic independent checkers (Prompt_V2 §5.3).

Contract: every checker returns a CheckerResult with a per-output verdict.
Checker *discrimination* (AUROC) is computed separately over labeled samples
(see metrics/auroc.py) — a single output's score is never an AUROC.
"""

from .base import Checker, CheckerRegistry, CheckerResult
from .citation_check import CitationChecker
from .numeric_recompute import NumericRecomputeChecker
from .schema_check import SchemaChecker
from .unit_test import UnitTestChecker

__all__ = [
    "Checker",
    "CheckerRegistry",
    "CheckerResult",
    "CitationChecker",
    "NumericRecomputeChecker",
    "SchemaChecker",
    "UnitTestChecker",
]
