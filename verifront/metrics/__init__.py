"""Metrics: AUROC (with explicit NA), task-clustered ΔSR, full-cost accounting."""

from .auroc import auroc, bootstrap_ci as auroc_bootstrap_ci, compute_auroc_or_na
from .cost import Price, cost_of, total_cost
from .effect import cluster_bootstrap_ci, delta_sr, summarize

__all__ = [
    "Price",
    "auroc",
    "auroc_bootstrap_ci",
    "cluster_bootstrap_ci",
    "compute_auroc_or_na",
    "cost_of",
    "delta_sr",
    "summarize",
    "total_cost",
]
