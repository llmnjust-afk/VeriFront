"""AUROC: hand-verified values, ties, explicit-NA rule, bootstrap determinism."""

from verifront.metrics.auroc import auroc, bootstrap_ci, compute_auroc_or_na


def test_auroc_hand_computed():
    # pos=[0.9, 0.8, 0.3], neg=[0.2, 0.4, 0.1]
    scores = [0.9, 0.8, 0.3, 0.2, 0.4, 0.1]
    labels = [1, 1, 1, 0, 0, 0]
    # pairs (pos>neg): 0.9 beats 3; 0.8 beats 3; 0.3 beats only 0.2,0.1 -> 2 => (3+3+2)/9 = 8/9
    assert abs(auroc(scores, labels) - 8 / 9) < 1e-12


def test_auroc_with_ties():
    scores = [0.5, 0.5, 0.5, 0.5]
    labels = [1, 1, 0, 0]
    assert abs(auroc(scores, labels) - 0.5) < 1e-12


def test_missing_class_returns_none_with_reason():
    res = compute_auroc_or_na([(0.9, 1), (0.8, 1), (0.7, 1)])
    assert res["auroc"] is None
    assert res["usable"] is False
    assert "missing_class" in res["reason"]


def test_perfect_separation_flagged(checker_samples):
    res = compute_auroc_or_na(checker_samples)
    assert res["auroc"] == 1.0
    assert res["separable_flag"] is True
    assert res["n_pos"] == 10 and res["n_neg"] == 10


def test_bootstrap_ci_contains_point_and_is_deterministic(checker_samples):
    b1 = bootstrap_ci(checker_samples, n_boot=500, seed=123)
    b2 = bootstrap_ci(checker_samples, n_boot=500, seed=123)
    assert b1 == b2
    assert b1["lo"] <= 1.0 <= b1["hi"]


def test_mixed_case_value():
    # pos=[0.6,0.2], neg=[0.4,0.8,0.3]
    # 0.6 beats 0.4, 0.3 (2); 0.2 beats nothing (0.2 < 0.3) -> 2/6 = 1/3
    assert abs(auroc([0.6, 0.2, 0.4, 0.8, 0.3], [1, 1, 0, 0, 0]) - 1 / 3) < 1e-12
