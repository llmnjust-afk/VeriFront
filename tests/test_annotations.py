"""Kappa, confusion matrix, label merge, and cost accounting."""

import math

from verifront.annotations.labels import (
    LabelRecord,
    cohen_kappa,
    confusion_matrix,
    merge_double_annotation,
)
from verifront.metrics.cost import Price, cost_of, total_cost


class TestKappa:
    def test_perfect_agreement(self):
        a = ["code_gen_repair"] * 5 + ["retrieval"] * 5
        assert cohen_kappa(a, a) == 1.0

    def test_known_value(self):
        # a=[x,x,x,y], b=[x,x,y,y]: po=3/4, pe=(3/4)(2/4)+(1/4)(2/4)=0.5 => kappa=0.5
        a = ["x", "x", "x", "y"]
        b = ["x", "x", "y", "y"]
        k = cohen_kappa(a, b)
        assert abs(k - 0.5) < 1e-12

    def test_degenerate_case_returns_none(self):
        assert cohen_kappa(["a", "a"], ["a", "a"]) is None  # pe == 1
        assert cohen_kappa([], []) is None

    def test_length_mismatch_raises(self):
        import pytest

        with pytest.raises(ValueError):
            cohen_kappa(["a"], ["a", "b"])


def test_confusion_matrix_counts():
    cm = confusion_matrix(["x", "x", "y"], ["x", "y", "y"])
    assert cm[("x", "x")] == 1 and cm[("x", "y")] == 1 and cm[("y", "y")] == 1


def test_merge_double_annotation():
    a = {
        "i1": LabelRecord("i1", "retrieval"),
        "i2": LabelRecord("i2", "numeric_stats"),
    }
    b = {
        "i1": LabelRecord("i1", "retrieval"),
        "i3": LabelRecord("i3", "retrieval"),
    }
    merged = merge_double_annotation(a, b)
    # i2/i3: labeled by only one annotator => "missing" (not disagreement)
    assert merged == {"i1": "retrieval", "i2": "missing", "i3": "missing"}


def test_label_validation_requires_evidence():
    bad = LabelRecord("i1", "retrieval", correctness="incorrect", evidence="")
    assert any("evidence" in e for e in bad.validate())
    good = LabelRecord("i1", "retrieval", correctness="correct", evidence="matches reference output")
    assert good.validate() == []


class TestCost:
    prices = {"frontier": Price("frontier", 2.0, 8.0), "local": Price("local", 0.0, 0.0)}

    def test_cost_of(self):
        # 1M prompt @ $2/1M + 1M completion @ $8/1M = $10
        assert math.isclose(cost_of(1_000_000, 1_000_000, self.prices["frontier"]), 10.0)

    def test_total_cost_includes_all_phases(self):
        rows = [
            {"model_id": "frontier", "prompt_tokens": 500_000, "completion_tokens": 100_000, "phase": "initial"},
            {"model_id": "frontier", "prompt_tokens": 500_000, "completion_tokens": 100_000, "phase": "continuation"},
            {"model_id": "local", "prompt_tokens": 10_000, "completion_tokens": 5_000, "phase": "replacement_step"},
        ]
        out = total_cost(rows, self.prices)
        # frontier: (0.5*2 + 0.1*8) * 2 = 3.6 ; local: 0
        assert math.isclose(out["total_usd"], 3.6)
        assert math.isclose(out["per_phase"]["initial"], 1.8)
        assert out["n_rows"] == 3
        assert out["unknown_models"] == []

    def test_unknown_model_is_reported(self):
        out = total_cost([{"model_id": "ghost", "prompt_tokens": 1, "completion_tokens": 1}], self.prices)
        assert out["unknown_models"] == ["ghost"]
        assert out["total_usd"] == 0.0
