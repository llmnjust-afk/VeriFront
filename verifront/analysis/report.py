"""Aggregate pilot artifacts into honest, boundary-aware summaries.

Reported quantities always carry their coverage/limits: pilot n is small,
cluster structure is respected, and "no data" is reported as no data — never
smoothed over (Prompt_V2 §8, §11).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Sequence

from ..metrics.effect import summarize as delta_summarize


def step_coverage_table(steps: Sequence[Any]) -> List[Dict[str, Any]]:
    counts = Counter(s.step_type for s in steps)
    total = sum(counts.values()) or 1
    return [
        {"step_type": t, "count": c, "fraction": round(c / total, 4)}
        for t, c in sorted(counts.items())
    ]


def recovery_summary(reports: Sequence[Any]) -> Dict[str, Any]:
    anchors = len(reports)
    recovered = sum(1 for r in reports if r.ok)
    failure_counts: Dict[str, int] = {}
    for r in reports:
        for ft in r.failure_types:
            failure_counts[ft] = failure_counts.get(ft, 0) + 1
    return {
        "anchors": anchors,
        "recovered": recovered,
        "recovery_rate": (recovered / anchors) if anchors else None,
        "failure_types": failure_counts,
    }


def delta_by_type(
    results: Sequence[Dict], step_type_of: Dict[str, str], min_n_for_interval: int = 8
) -> List[Dict[str, Any]]:
    """Descriptive per-type ΔSR. Pilot n is small: intervals are reported only
    when a type has enough task support, and always labeled descriptive."""
    by_type: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        st = step_type_of.get(r["step_id"], "unassignable")
        by_type[st][r["arm"]].append(r)
    out = []
    for st in sorted(by_type):
        arms = by_type[st]
        records = [
            {"task_id": r["task_id"], "arm": arm, "success": r.get("success")}
            for arm in ("control", "treatment")
            for r in arms.get(arm, [])
        ]
        summ = delta_summarize(records)
        row: Dict[str, Any] = {
            "step_type": st,
            "n_control": len(arms.get("control", [])),
            "n_treatment": len(arms.get("treatment", [])),
            "delta_sr": summ["delta_sr"],
            "n_tasks_used": summ["n_tasks_used"],
            "descriptive_only": True,
        }
        if summ["n_tasks_used"] >= min_n_for_interval:
            row["ci95"] = summ["ci95"]
        else:
            row["ci95"] = None
            row["ci_note"] = f"task support < {min_n_for_interval}; no interval reported"
        out.append(row)
    return out


def checker_discrimination_table(auroc_results: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """auroc_results: {checker_name: compute_auroc_or_na output}."""
    rows = []
    for name in sorted(auroc_results):
        r = auroc_results[name]
        rows.append(
            {
                "checker": name,
                "auroc": r.get("auroc"),
                "usable": r.get("usable"),
                "reason": r.get("reason"),
                "n_samples": r.get("n_samples"),
                "separable_flag": r.get("separable_flag"),
            }
        )
    return rows


def evaluate_gates(gates: Dict[str, float], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Advisory go/refine/pivot hints per Prompt_V2 §8.3 — engineering gates
    only; they do NOT certify scientific claims."""
    recovery = metrics.get("recovery_rate")
    kappa = metrics.get("kappa")
    has_labels = metrics.get("has_independent_correctness_labels", False)
    checks = {
        "recovery_rate>=pilot_min": (recovery is not None and recovery >= gates.get("recovery_rate_pilot_min", 0.90)),
        "kappa>=min": (kappa is not None and kappa >= gates.get("kappa_min", 0.70)),
        "independent_correctness_labels": bool(has_labels),
    }
    if all(checks.values()):
        verdict = "GO: scale to P4 and plan a formal power analysis"
    elif checks["independent_correctness_labels"] and (recovery is None or recovery >= 0.5):
        verdict = "REFINE: fix recovery/measurement before scaling"
    else:
        verdict = "REFINE/STOP: infrastructure or measurement not trustworthy yet"
    return {"checks": checks, "verdict": verdict, "advisory_only": True}


def render_pilot_report_md(sections: Dict[str, Any]) -> str:
    lines = ["# VeriFront Pilot Report (auto-generated skeleton)", ""]
    for title, content in sections.items():
        lines.append(f"## {title}")
        lines.append("")
        if isinstance(content, str):
            lines.append(content)
        else:
            lines.append("```json")
            import json as _json

            lines.append(_json.dumps(content, ensure_ascii=False, indent=2, default=str))
            lines.append("```")
        lines.append("")
    lines.append("> Boundary note: pilot-scale results are exploratory; report them with their")
    lines.append("> coverage, exclusions, and failure modes. Do not overclaim (Prompt_V2 §0.2, §8).")
    return "\n".join(lines)
