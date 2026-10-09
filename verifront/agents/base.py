"""Shared data structures for agents (no network I/O here)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import yaml


@dataclass
class StepOutput:
    """Output of one generated step (treatment or control arm)."""

    text: str
    model_id: str
    token_usage: Dict[str, int] = field(default_factory=dict)  # {prompt, completion}
    tool_args: Optional[Dict[str, Any]] = None
    latency_s: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None  # raw provider response (for debugging; strip before sharing)


@dataclass
class ContinuationOutcome:
    """Outcome of continuing a task after the replaced step."""

    success: Optional[bool]  # None = not evaluated yet
    tokens: Dict[str, int] = field(default_factory=dict)
    latency_s: Optional[float] = None
    failure_reason: Optional[str] = None
    trajectory_ref: Optional[str] = None


@dataclass
class ContinuationSpec:
    """Continuation settings that MUST be identical across paired arms.

    The paired runner hashes this object and stamps the digest into every arm
    result, so unequal continuation conditions cannot silently mix into one
    causal comparison (Prompt_V2 §6.1).
    """

    continuation_model_id: str
    max_tokens: int
    tool_budget: int
    max_steps: int
    seed: Optional[int] = None
    notes: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "continuation_model_id": self.continuation_model_id,
            "max_tokens": self.max_tokens,
            "tool_budget": self.tool_budget,
            "max_steps": self.max_steps,
            "seed": self.seed,
            "notes": self.notes,
        }


def load_models_config(path) -> Dict[str, Any]:
    """Load configs/models.yaml and sanity-check required fields."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    frontier = cfg.get("frontier") or {}
    if frontier.get("model_id") and not frontier.get("snapshot"):
        raise ValueError(
            "frontier.model_id is set but snapshot is null: "
            "a fixed snapshot is required (never rely on a floating alias)."
        )
    for m in cfg.get("local") or []:
        if not m.get("endpoint"):
            raise ValueError(f"local model {m.get('name')!r} missing endpoint")
    return cfg
