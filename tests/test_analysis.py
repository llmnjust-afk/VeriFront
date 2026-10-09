"""Report aggregation + gate evaluation honesty (no overclaiming)."""

from verifront.analysis.report import (
    checker_discrimination_table,
    delta_by_type,
    evaluate_gates,
    recovery_summary,
    render_pilot_report_md,
    step_coverage_table,
)
from verifront.state.replay import StateEquivalenceChecker
from verifront.state.capture import PreState
from verifront.traces.steps import SemanticStep


def test_step_coverage_table():
    steps = [
        SemanticStep("s1", ["a1"], "retrieval"),
        SemanticStep("s2", ["a2"], "retrieval"),
        SemanticStep("s3", ["a3"], "unassignable"),
    ]
    table = step_coverage_table(steps)
    d = {r["step_type"]: r for r in table}
    assert d["retrieval"]["count"] == 2
    assert abs(d["unassignable"]["fraction"] - 1 / 3) < 1e-3


def test_recovery_summary_matches_checker():
    checker = StateEquivalenceChecker()
    reports = [
        checker.compare(PreState(), PreState(), anchor_id="ok"),
        checker.compare(PreState(), PreState(process_probe={"v": 1}), anchor_id="bad"),
    ]
    s = recovery_summary(reports)
    assert s["recovery_rate"] == 0.5
    assert s["failure_types"] == {"process_probe:mismatch": 1}


def test_delta_by_type_hides_ci_for_small_support():
    results = [
        {"step_id": "s1", "task_id": "t1", "arm": "control", "success": True},
        {"step_id": "s1", "task_id": "t1", "arm": "treatment", "success": False},
    ]
    rows = delta_by_type(results, {"s1": "retrieval"}, min_n_for_interval=8)
    assert rows[0]["ci95"] is None
    assert rows[0]["descriptive_only"] is True
    assert "task support" in rows[0]["ci_note"]


def test_checker_table_reports_na_openly():
    table = checker_discrimination_table(
        {
            "ut": {"auroc": 0.87, "usable": True, "n_samples": 40},
            "cite": {"auroc": None, "usable": False, "reason": "missing_class (pos=5, neg=0)"},
        }
    )
    cite = [r for r in table if r["checker"] == "cite"][0]
    assert cite["auroc"] is None and "missing_class" in cite["reason"]


def test_gates_are_advisory_and_honest():
    gates = {"recovery_rate_pilot_min": 0.90, "kappa_min": 0.70}
    go = evaluate_gates(gates, {"recovery_rate": 0.95, "kappa": 0.8, "has_independent_correctness_labels": True})
    assert go["verdict"].startswith("GO")
    assert go["advisory_only"] is True
    refine = evaluate_gates(gates, {"recovery_rate": 0.5, "kappa": 0.5, "has_independent_correctness_labels": False})
    assert "REFINE" in refine["verdict"]


def test_render_report_contains_boundary_note():
    md = render_pilot_report_md({"Coverage": {"a": 1}})
    assert "Boundary note" in md
    assert "## Coverage" in md
