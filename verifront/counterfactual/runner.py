"""Paired counterfactual replacement runner (Prompt_V2 §6.1).

Invariants enforced structurally:
- ONE ContinuationSpec object is shared by both arms and its digest is stamped
  into every ArmResult — unequal continuation conditions cannot silently mix;
- the pre-state is captured once and its digest recorded for both arms;
- the caller supplies execute callbacks; this module never talks to a provider.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..state.capture import PreState
from .sampling import ReplacementCandidate


def digest_of(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


@dataclass
class ArmResult:
    task_id: str
    trajectory_id: str
    step_id: str
    arm: str                     # "control" (frontier resample) | "treatment" (local)
    step_model_id: str
    rep: int
    success: Optional[bool]
    tokens: Dict[str, int] = field(default_factory=dict)
    latency_s: Optional[float] = None
    failure_reason: Optional[str] = None
    prestate_digest: str = ""
    continuation_digest: str = ""


class PairedReplacementRunner:
    """execute_step_fn(pre_state, arm, rep) -> {"model_id", "tokens", "latency_s",
    "failure_reason"};  continue_fn(pre_state, ContinuationSpec) ->
    {"success", "tokens", "latency_s", "failure_reason"}."""

    def __init__(
        self,
        execute_step_fn: Callable[[PreState, str, int], Dict[str, Any]],
        continue_fn: Callable[[PreState, Any], Dict[str, Any]],
    ):
        self.execute_step_fn = execute_step_fn
        self.continue_fn = continue_fn

    def run_pair(
        self,
        pre_state: PreState,
        candidate: ReplacementCandidate,
        continuation_spec: Any,          # agents.base.ContinuationSpec (duck-typed; must have as_dict)
        reps: int = 1,
    ) -> List[ArmResult]:
        if pre_state is None:
            raise ValueError("pre_state is required: paired arms must start from a captured state")
        if reps < 1:
            raise ValueError("reps must be >= 1")

        pre_digest = digest_of(
            {
                "fs": pre_state.fs_manifest,
                "env": pre_state.env_digest,
                "ctx": pre_state.agent_context,
                "probe": pre_state.process_probe,
            }
        )
        cont_digest = digest_of(continuation_spec.as_dict())

        results: List[ArmResult] = []
        for rep in range(reps):
            for arm in ("control", "treatment"):  # fixed order: control first, then treatment
                step_info = self.execute_step_fn(pre_state, arm, rep)
                outcome = self.continue_fn(pre_state, continuation_spec)
                results.append(
                    ArmResult(
                        task_id=candidate.task_id,
                        trajectory_id=candidate.trajectory_id,
                        step_id=candidate.step_id,
                        arm=arm,
                        step_model_id=str(step_info.get("model_id", "")),
                        rep=rep,
                        success=outcome.get("success"),
                        tokens=dict(outcome.get("tokens") or {}),
                        latency_s=outcome.get("latency_s"),
                        failure_reason=outcome.get("failure_reason"),
                        prestate_digest=pre_digest,
                        continuation_digest=cont_digest,
                    )
                )
        # both arms must share the same prestate & continuation digests
        pre_set = {r.prestate_digest for r in results}
        cont_set = {r.continuation_digest for r in results}
        if len(pre_set) != 1 or len(cont_set) != 1:
            raise RuntimeError("internal error: arm digests diverged")
        return results
