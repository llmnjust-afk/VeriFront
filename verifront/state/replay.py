"""State equivalence checking (Prompt_V2 §4.3).

Design rules enforced here:
- files / environment / agent_context are REQUIRED dimensions; any mismatch
  fails the whole anchor.
- process_probe mismatches fail too (probes are how we detect invisible state
  divergence that docker commit cannot see).
- external state that cannot be controlled is reported as "unsupported" —
  recorded, but not counted as a recovery failure (it is a scope limitation).
- semantic-neutral differences (timestamps, temp paths) are removed ONLY via
  pre-registered normalization rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .capture import PreState, agent_context_digest

NormalizationRule = Dict[str, str]  # {"name": ..., "pattern": ..., "replacement": ...}

DEFAULT_NORMALIZATION_RULES: List[NormalizationRule] = [
    {"name": "iso_timestamp", "pattern": r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", "replacement": "<TS>"},
    {"name": "unix_tmp_path", "pattern": r"/tmp/[\w./-]+", "replacement": "<TMP>"},
]

REQUIRED_DIMENSIONS = ("files", "environment", "agent_context")
ALL_DIMENSIONS = REQUIRED_DIMENSIONS + ("process_probe", "external")


def normalize_text(text: str, rules: List[NormalizationRule]) -> str:
    out = text
    for r in rules:
        out = re.sub(r["pattern"], r["replacement"], out)
    return out


@dataclass
class DimensionResult:
    dimension: str
    status: str  # match | mismatch | unsupported | error
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EquivalenceReport:
    anchor_id: str
    results: List[DimensionResult]

    @property
    def ok(self) -> bool:
        return all(r.status in ("match", "unsupported") for r in self.results)

    @property
    def failure_types(self) -> List[str]:
        return [f"{r.dimension}:{r.status}" for r in self.results if r.status not in ("match", "unsupported")]


class StateEquivalenceChecker:
    def __init__(self, normalization_rules: Optional[List[NormalizationRule]] = None):
        self.rules = normalization_rules if normalization_rules is not None else list(DEFAULT_NORMALIZATION_RULES)

    def compare(self, pre: PreState, post: PreState, anchor_id: str = "anchor") -> EquivalenceReport:
        results: List[DimensionResult] = []
        results.append(self._compare_files(pre, post))
        results.append(self._compare_env(pre, post))
        results.append(self._compare_context(pre, post))
        results.append(self._compare_probe(pre, post))
        results.append(self._compare_external(pre, post))
        return EquivalenceReport(anchor_id=anchor_id, results=results)

    def _compare_files(self, pre: PreState, post: PreState) -> DimensionResult:
        a, b = pre.fs_manifest, post.fs_manifest
        problems: List[str] = []
        for key in sorted(set(a) | set(b)):
            ra, rb = a.get(key), b.get(key)
            if ra is None or rb is None:
                problems.append(f"manifest key only on one side: {key}")
                continue
            if ra.get("missing") or rb.get("missing"):
                problems.append(f"missing file: {key}")
                continue
            if ra.get("sha256") != rb.get("sha256"):
                problems.append(f"sha256 mismatch: {key}")
        status = "match" if not problems else "mismatch"
        return DimensionResult("files", status, {"problems": problems[:20]})

    def _compare_env(self, pre: PreState, post: PreState) -> DimensionResult:
        if pre.env_digest != post.env_digest:
            diffs = {
                k: (pre.env_digest.get(k), post.env_digest.get(k))
                for k in set(pre.env_digest) | set(post.env_digest)
                if pre.env_digest.get(k) != post.env_digest.get(k)
            }
            return DimensionResult("environment", "mismatch", {"diffs": diffs})
        return DimensionResult("environment", "match")

    def _compare_context(self, pre: PreState, post: PreState) -> DimensionResult:
        na = agent_context_digest(normalize_text(pre.agent_context, self.rules))
        nb = agent_context_digest(normalize_text(post.agent_context, self.rules))
        if na != nb:
            return DimensionResult("agent_context", "mismatch", {})
        return DimensionResult("agent_context", "match")

    def _compare_probe(self, pre: PreState, post: PreState) -> DimensionResult:
        if pre.process_probe is None and post.process_probe is None:
            return DimensionResult("process_probe", "unsupported", {"reason": "no probes defined"})
        problems: List[str] = []
        pa, pb = pre.process_probe or {}, post.process_probe or {}
        for key in sorted(set(pa) | set(pb)):
            va, vb = pa.get(key, "<absent>"), pb.get(key, "<absent>")
            if va != vb:
                problems.append(f"probe {key}: {va!r} != {vb!r}")
        status = "match" if not problems else "mismatch"
        return DimensionResult("process_probe", status, {"problems": problems[:20]})

    def _compare_external(self, pre: PreState, post: PreState) -> DimensionResult:
        if pre.external is None or post.external is None:
            return DimensionResult("external", "unsupported", {"reason": "external state not controlled"})
        if pre.external != post.external:
            return DimensionResult("external", "mismatch", {})
        return DimensionResult("external", "match")


def aggregate_recovery(reports: List[EquivalenceReport]) -> Dict[str, Any]:
    ok = sum(1 for r in reports if r.ok)
    per_dim: Dict[str, Dict[str, int]] = {}
    for r in reports:
        for d in r.results:
            per_dim.setdefault(d.dimension, {})
            per_dim[d.dimension][d.status] = per_dim[d.dimension].get(d.status, 0) + 1
    failure_counts: Dict[str, int] = {}
    for r in reports:
        for ft in r.failure_types:
            failure_counts[ft] = failure_counts.get(ft, 0) + 1
    return {
        "anchors": len(reports),
        "recovered": ok,
        "recovery_rate": (ok / len(reports)) if reports else None,
        "per_dimension": per_dim,
        "failure_counts": failure_counts,
    }
