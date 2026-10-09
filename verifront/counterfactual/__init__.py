"""Counterfactual replacement: pre-registered sampling and paired execution."""

from ..agents.base import ContinuationSpec
from .runner import ArmResult, PairedReplacementRunner
from .sampling import ReplacementCandidate, sample_replacement_points

__all__ = [
    "ArmResult",
    "ContinuationSpec",
    "PairedReplacementRunner",
    "ReplacementCandidate",
    "sample_replacement_points",
]
