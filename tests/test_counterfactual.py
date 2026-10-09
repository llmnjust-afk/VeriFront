"""Counterfactual runner + pre-registered sampling (§10.2)."""

import json

import pytest

from verifront.agents.base import ContinuationSpec
from verifront.counterfactual.runner import PairedReplacementRunner, digest_of
from verifront.counterfactual.sampling import ReplacementCandidate, sample_replacement_points
from verifront.state.capture import PreState


def _cand(task, step, stype, pos, n, recoverable=True, reason=None):
    return ReplacementCandidate(
        task_id=task, trajectory_id=f"{task}-traj", step_id=step, position=pos,
        n_actions_in_trajectory=n, step_type=stype, recoverable=recoverable, exclude_reason=reason,
    )


class TestSampling:
    def test_deterministic_with_seed(self):
        cands = [_cand(f"t{i}", f"s{i}", "code_gen_repair", i, 10) for i in range(10)]
        a = sample_replacement_points(cands, 5, seed=7)
        b = sample_replacement_points(cands, 5, seed=7)
        c = sample_replacement_points(cands, 5, seed=8)
        assert [x.step_id for x in a[0]] == [x.step_id for x in b[0]]
        assert [x.step_id for x in a[0]] != [x.step_id for x in c[0]]

    def test_non_recoverable_excluded_with_reason(self):
        cands = [
            _cand("t1", "s1", "retrieval", 0, 5, recoverable=False, reason="unrecoverable tool state"),
            _cand("t1", "s2", "retrieval", 1, 5),
        ]
        selected, excluded, record = sample_replacement_points(cands, 2, seed=1)
        assert [c.step_id for c in selected] == ["s2"]
        assert excluded[0][1] == "unrecoverable tool state"
        assert record["excluded_count"] == 1

    def test_stratified_by_step_type(self):
        cands = (
            [_cand(f"t{i}", f"r{i}", "retrieval", i, 10) for i in range(6)]
            + [_cand(f"t{i}", f"c{i}", "code_gen_repair", i, 10) for i in range(4)]
        )
        selected, _, record = sample_replacement_points(cands, 5, seed=3, stratify_by=("step_type",))
        types = {c.step_type for c in selected}
        assert types == {"retrieval", "code_gen_repair"}  # both strata represented
        assert record["selected_count"] == 5
        assert record["strata_eligible"][repr(("retrieval",))] == 6

    def test_pre_registration_record_is_serializable(self):
        cands = [_cand("t1", "s1", "tool_args", 0, 4)]
        _, _, record = sample_replacement_points(cands, 1, seed=0)
        blob = json.dumps(record)  # must not raise
        assert "seed" in blob and "stratify_by" in blob


class TestPairedRunner:
    def _pre(self):
        return PreState(agent_context="ctx", fs_manifest={}, env_digest={"python": "3.10"}, process_probe={"v": 1})

    def test_both_arms_share_prestate_and_continuation_digest(self):
        calls = []

        def execute(pre, arm, rep):
            calls.append(arm)
            return {"model_id": "frontier" if arm == "control" else "local-a", "tokens": {"prompt": 10, "completion": 2}}

        def continue_fn(pre, spec):
            return {"success": True, "tokens": {"prompt": 100, "completion": 20}, "latency_s": 1.0}

        runner = PairedReplacementRunner(execute, continue_fn)
        spec = ContinuationSpec(continuation_model_id="frontier", max_tokens=1024, tool_budget=10, max_steps=20, seed=0)
        results = runner.run_pair(self._pre(), _cand("t1", "s1", "retrieval", 0, 5), spec, reps=2)
        assert len(results) == 4  # 2 reps x 2 arms
        assert {r.arm for r in results} == {"control", "treatment"}
        assert len({r.prestate_digest for r in results}) == 1
        assert len({r.continuation_digest for r in results}) == 1
        assert calls == ["control", "treatment", "control", "treatment"]

    def test_continuation_digest_changes_with_spec(self):
        s1 = ContinuationSpec("frontier", 1024, 10, 20, seed=0)
        s2 = ContinuationSpec("frontier", 2048, 10, 20, seed=0)
        assert digest_of(s1.as_dict()) != digest_of(s2.as_dict())

    def test_missing_prestate_refuses(self):
        runner = PairedReplacementRunner(lambda *a: {}, lambda *a: {})
        with pytest.raises(ValueError):
            runner.run_pair(None, _cand("t1", "s1", "retrieval", 0, 5),
                            ContinuationSpec("m", 1, 1, 1))

    def test_unevaluated_success_propagates(self):
        runner = PairedReplacementRunner(
            lambda pre, arm, rep: {"model_id": "m"},
            lambda pre, spec: {"success": None, "failure_reason": "eval crashed"},
        )
        results = runner.run_pair(self._pre(), _cand("t1", "s1", "retrieval", 0, 5),
                                  ContinuationSpec("m", 1, 1, 1))
        assert all(r.success is None and r.failure_reason == "eval crashed" for r in results)
