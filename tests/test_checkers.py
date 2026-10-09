"""Checker behavior: pass/fail correctness, determinism, timeout handling,
and the registry coverage map (§10.2)."""

import pytest

from verifront.checkers.base import CheckerRegistry
from verifront.checkers.citation_check import CitationChecker
from verifront.checkers.numeric_recompute import NumericRecomputeChecker
from verifront.checkers.schema_check import SchemaChecker
from verifront.checkers.unit_test import UnitTestChecker


class TestSchemaChecker:
    def test_pass_and_fail(self):
        c = SchemaChecker("sch", required={"mean": (int, float)}, ranges={"mean": (0, 100)})
        assert c.check({"mean": 3.5}).passed is True
        r = c.check({"mean": "high"})
        assert r.passed is False
        assert any("wrong type" in p for p in r.details["problems"])
        r2 = c.check({"mean": 150})
        assert any("out of range" in p for p in r2.details["problems"])
        r3 = c.check({})
        assert any("missing key" in p for p in r3.details["problems"])


class TestUnitTestChecker:
    def test_passing_code(self):
        c = UnitTestChecker("ut", test_code="assert f(2) == 4\n")
        res = c.check({"code": "def f(x):\n    return x * 2\n"})
        assert res.passed is True
        assert res.details["status"] == "passed"
        assert res.cost_seconds >= 0

    def test_failing_code_detected(self):
        c = UnitTestChecker("ut", test_code="assert f(2) == 5\n")
        res = c.check({"code": "def f(x):\n    return x * 2\n"})
        assert res.passed is False

    def test_timeout_is_detected_not_hanging(self):
        c = UnitTestChecker("ut", test_code="assert True\n", timeout_s=2)
        res = c.check({"code": "import time\ntime.sleep(30)\n"})
        assert res.passed is False
        assert res.details["status"] == "timeout"

    def test_empty_code_fails(self):
        c = UnitTestChecker("ut", test_code="assert True\n")
        assert c.check({"code": ""}).passed is False


class TestNumericRecompute:
    def test_correct_and_wrong(self):
        def recompute(inputs):
            return {"mean": sum(inputs["xs"]) / len(inputs["xs"])}

        c = NumericRecomputeChecker("recomp", recompute, fields=["mean"])
        ok = c.check({"inputs": {"xs": [1, 2, 3]}, "mean": 2.0})
        assert ok.passed is True
        bad = c.check({"inputs": {"xs": [1, 2, 3]}, "mean": 9.0})
        assert bad.passed is False
        assert any("value mismatch" in p for p in bad.details["problems"])
        missing = c.check({"inputs": {"xs": [1, 2, 3]}})
        assert missing.passed is False

    def test_recompute_exception_recorded(self):
        def boom(inputs):
            raise KeyError("bad inputs")

        c = NumericRecomputeChecker("recomp", boom, fields=["mean"])
        res = c.check({"inputs": {}, "mean": 1})
        assert res.passed is False
        assert any("recompute raised" in p for p in res.details["problems"])


class TestCitationChecker:
    def test_ok_mismatch_missing(self):
        c = CitationChecker("cite", {"doc1": "The mitochondria is the powerhouse of the cell."})
        assert c.check({"citations": [{"doc_id": "doc1", "quote": "powerhouse of the cell"}]}).passed is True
        r = c.check({"citations": [{"doc_id": "doc1", "quote": "invented text"}]})
        assert r.passed is False and any("quote not found" in p for p in r.details["problems"])
        r2 = c.check({"citations": [{"doc_id": "ghost", "quote": "x"}]})
        assert any("unknown doc_id" in p for p in r2.details["problems"])
        r3 = c.check({"citations": []})
        assert r3.passed is False and any("no citations" in p for p in r3.details["problems"])


def test_registry_coverage_and_low_cost_measurement():
    reg = CheckerRegistry()
    reg.register("code_gen_repair", UnitTestChecker("ut", "assert True\n"))
    reg.register("numeric_stats", NumericRecomputeChecker("r", lambda i: {}, ["x"]))
    reg.register("doc_parse_convert", SchemaChecker("s", required={"rows": (int,)}))
    assert reg.coverage_map(["code_gen_repair", "numeric_stats", "retrieval"]) == {
        "code_gen_repair": 1,
        "numeric_stats": 1,
        "retrieval": 0,
    }
    results = reg.run_all("doc_parse_convert", {"rows": 5})
    assert len(results) == 1 and results[0].passed is True
    assert results[0].extra_model_calls == 0  # deterministic checks cost no model calls
