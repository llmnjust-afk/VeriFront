"""Annotation schemas and double-annotation agreement statistics."""

from .labels import (
    CORRECTNESS_VALUES,
    LabelRecord,
    cohen_kappa,
    confusion_matrix,
    merge_double_annotation,
)

__all__ = [
    "CORRECTNESS_VALUES",
    "LabelRecord",
    "cohen_kappa",
    "confusion_matrix",
    "merge_double_annotation",
]
