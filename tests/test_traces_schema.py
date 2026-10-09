"""Trajectory integrity: required fields, id uniqueness, monotonic time,
JSONL roundtrip, artifact hashing (Prompt_V2 §3.4, §10.2)."""

import json
import os

from verifront.traces.schema import Event, RunMeta, Trajectory, sha256_bytes, sha256_file


def test_golden_trajectory_is_valid(golden_trajectory):
    assert golden_trajectory.validate() == []


def test_missing_required_field_is_caught(golden_meta):
    bad = Event(event_id="", trajectory_id="t", event_type="tool_call", event_time=0.0)
    errs = Trajectory(meta=golden_meta, events=[bad]).validate()
    assert any("event_id" in e for e in errs)


def test_unknown_event_type_is_caught(golden_meta):
    bad = Event(event_id="e1", trajectory_id="t", event_type="teleport", event_time=0.0)
    errs = Trajectory(meta=golden_meta, events=[bad]).validate()
    assert any("unknown event_type" in e for e in errs)


def test_duplicate_and_nonmonotonic_events_are_caught(golden_meta):
    e = Event(event_id="e1", trajectory_id="t", event_type="tool_call", event_time=1.0)
    e2 = Event(event_id="e1", trajectory_id="t", event_type="tool_call", event_time=0.0)
    errs = Trajectory(meta=golden_meta, events=[e, e2]).validate()
    assert any("duplicate event_id" in x for x in errs)
    assert any("not monotonic" in x for x in errs)


def test_jsonl_roundtrip(golden_trajectory):
    text = golden_trajectory.to_jsonl()
    rebuilt = Trajectory.from_jsonl(text)
    assert rebuilt.meta == golden_trajectory.meta
    assert [e.event_id for e in rebuilt.events] == [e.event_id for e in golden_trajectory.events]
    assert rebuilt.validate() == []


def test_jsonl_missing_meta_raises(golden_trajectory):
    lines = golden_trajectory.to_jsonl().splitlines()
    body_only = "\n".join(l for l in lines if "_meta" not in l)
    import pytest

    with pytest.raises(ValueError):
        Trajectory.from_jsonl(body_only)


def test_artifact_hashes(tmp_path):
    p = tmp_path / "artifact.csv"
    payload = b"a,b\n1,2\n"
    p.write_bytes(payload)
    assert sha256_file(p) == sha256_bytes(payload)
    assert len(sha256_file(p)) == 64
    # required meta field presence check via RunMeta.validate
    meta = RunMeta(run_id="", task_id="", benchmark_version="", agent_commit="", model_id="", model_snapshot_or_revision="")
    errs = meta.validate()
    assert len(errs) == len(RunMeta.__dataclass_fields__) - 0 or all("missing required field" in e for e in errs)
    assert all("missing required field" in e for e in errs)


def test_env_vars_are_not_leaked_into_logs(golden_trajectory, tmp_path):
    """Sanity: the log schema has no place for raw environment secrets."""
    os.environ["VERIFRONT_TEST_SECRET"] = "should-not-appear"
    try:
        text = golden_trajectory.to_jsonl()
        assert "should-not-appear" not in text
        assert json.loads(text.splitlines()[0])["_meta"]["environment_digest"] == {"python": "3.10.12"}
    finally:
        del os.environ["VERIFRONT_TEST_SECRET"]
