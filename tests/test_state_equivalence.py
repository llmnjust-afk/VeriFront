"""State equivalence: perturbations MUST be detected, not silently passed;
semantic-neutral diffs are removed only by registered rules (§10.2)."""

from verifront.state.capture import PreState
from verifront.state.replay import (
    DEFAULT_NORMALIZATION_RULES,
    StateEquivalenceChecker,
    aggregate_recovery,
)


def _state(fs=None, ctx="hello", probe=None, external=None, env=None):
    return PreState(
        fs_manifest=fs or {},
        env_digest=env or {"python": "3.10"},
        agent_context=ctx,
        process_probe=probe,
        external=external,
    )


def test_identical_states_match():
    checker = StateEquivalenceChecker()
    report = checker.compare(_state(), _state(), anchor_id="a1")
    assert report.ok
    assert report.failure_types == []


def test_file_perturbation_is_detected():
    checker = StateEquivalenceChecker()
    fs = {"out.csv": {"sha256": "aa", "size": 3, "missing": False}}
    pre = _state(fs=fs)
    post = _state(fs={"out.csv": {"sha256": "bb", "size": 3, "missing": False}})
    report = checker.compare(pre, post, anchor_id="a2")
    assert not report.ok
    assert "files:mismatch" in report.failure_types


def test_missing_file_is_detected():
    checker = StateEquivalenceChecker()
    fs = {"out.csv": {"sha256": "aa", "size": 3, "missing": False}}
    post = _state(fs={"out.csv": {"missing": True}})
    report = checker.compare(_state(fs=fs), post, anchor_id="a3")
    assert not report.ok
    files_dim = [r for r in report.results if r.dimension == "files"][0]
    assert any("missing file" in p for p in files_dim.details["problems"])


def test_process_probe_divergence_is_detected():
    """docker commit cannot see memory; probes are the sentinel (§4.2)."""
    checker = StateEquivalenceChecker()
    pre = _state(probe={"kernel_var": 1})
    post = _state(probe={"kernel_var": 2})
    report = checker.compare(pre, post, anchor_id="a4")
    assert not report.ok
    assert "process_probe:mismatch" in report.failure_types


def test_timestamp_normalization_requires_registered_rule():
    checker = StateEquivalenceChecker(normalization_rules=[])  # no rules => exact match required
    report = checker.compare(_state(ctx="run at 2026-01-01T00:00:00Z"), _state(ctx="run at 2026-01-01T00:00:09Z"))
    assert not report.ok

    checker2 = StateEquivalenceChecker(normalization_rules=list(DEFAULT_NORMALIZATION_RULES))
    report2 = checker2.compare(_state(ctx="run at 2026-01-01T00:00:00Z"), _state(ctx="run at 2026-01-01T00:00:09Z"))
    assert report2.ok  # normalized away by the pre-registered iso_timestamp rule


def test_uncontrolled_external_is_unsupported_not_failure():
    checker = StateEquivalenceChecker()
    report = checker.compare(_state(external=None), _state(external=None), anchor_id="a5")
    assert report.ok  # unsupported dims are scope limitations, reported but not failures
    dims = {r.dimension: r.status for r in report.results}
    assert dims["external"] == "unsupported"


def test_aggregate_recovery_rate():
    checker = StateEquivalenceChecker()
    reports = [
        checker.compare(_state(), _state(), anchor_id="ok1"),
        checker.compare(_state(), _state(), anchor_id="ok2"),
        checker.compare(_state(), _state(probe={"v": 1}), anchor_id="bad"),
    ]
    agg = aggregate_recovery(reports)
    assert agg["anchors"] == 3
    assert agg["recovered"] == 2
    assert abs(agg["recovery_rate"] - 2 / 3) < 1e-9
    assert agg["failure_counts"].get("process_probe:mismatch") == 1
