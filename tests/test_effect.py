"""ΔSR task-level clustering: exclusions reported, CI contains point estimate,
bootstrap resamples tasks (not instances)."""

import random

from verifront.metrics.effect import cluster_bootstrap_ci, delta_sr, summarize


def test_point_estimate_hand_computed(replacement_records):
    res = delta_sr(replacement_records)
    assert abs(res["delta_sr"] - 0.0) < 1e-12
    assert res["n_tasks_used"] == 3
    assert res["n_tasks_excluded"] == 1
    assert res["excluded_task_ids"] == ["t4"]
    assert res["n_instances"] == 9  # all 9 evaluated runs count (t4's single run included)


def test_unknown_arm_raises():
    import pytest

    with pytest.raises(ValueError):
        delta_sr([{"task_id": "t", "arm": "mystery", "success": True}])


def test_none_success_excluded_from_math(replacement_records):
    recs = replacement_records + [{"task_id": "t1", "arm": "control", "success": None}]
    res = delta_sr(recs)
    assert abs(res["delta_sr"]) < 1e-12  # None run did not change the estimate


def test_cluster_bootstrap_is_task_level():
    """If resampling were instance-level, duplicating one task's many instances
    would shift the CI toward that task. We verify the unit count instead:
    n_tasks in CI metadata equals the number of distinct tasks."""
    recs = []
    for t in range(10):
        for _ in range(5):
            recs.append({"task_id": f"t{t}", "arm": "control", "success": t % 2 == 0})
            recs.append({"task_id": f"t{t}", "arm": "treatment", "success": t % 2 == 1})
    res = delta_sr(recs)
    ci = cluster_bootstrap_ci(res["task_deltas"], n_boot=300, seed=1)
    assert ci["n_tasks"] == 10
    assert ci["lo"] <= res["delta_sr"] <= ci["hi"]


def test_summarize_deterministic_and_honest(replacement_records):
    s1 = summarize(replacement_records, seed=5, n_boot=200)
    s2 = summarize(replacement_records, seed=5, n_boot=200)
    assert s1["ci95"] == s2["ci95"]
    assert "task-clustered" in s1["note"]


def test_empty_records_give_none_not_zero():
    res = delta_sr([])
    assert res["delta_sr"] is None
    assert cluster_bootstrap_ci([], n_boot=10)["lo"] is None
