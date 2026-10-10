"""Shared fixtures: synthetic golden trajectory, labeled checker outputs,
paired replacement records."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from verifront.traces.schema import Event, RunMeta, Trajectory  # noqa: E402


@pytest.fixture(autouse=True)
def _open_traverse_chain(tmp_path):
    """When running as root, sandboxed agent steps drop to `nobody`, which needs
    +x on every ancestor of tmp_path to reach the workdir. Open the chain for
    every test; harmless for non-sandbox tests."""
    if os.geteuid() == 0:
        p = tmp_path.resolve()
        while p != p.parent:
            try:
                os.chmod(p, 0o751)
            except OSError:
                pass
            if p == Path("/tmp"):
                break
            p = p.parent
    yield


@pytest.fixture()
def golden_meta() -> RunMeta:
    return RunMeta(
        run_id="run-001",
        task_id="SAB-demo-01",
        benchmark_version="SAB-verified-pinned",
        agent_commit="deadbeef",
        model_id="frontier-model",
        model_snapshot_or_revision="2026-01-01-snapshot",
        sampling_config={"seed": 42},
        environment_digest={"python": "3.10.12"},
    )


@pytest.fixture()
def golden_trajectory(golden_meta) -> Trajectory:
    """12 events: 2 messages + 3 tool actions (call+result pairs) + 1 file change."""
    evs = []
    spec = [
        ("agent_message", None, None),
        ("tool_call", "python", {"code": "df = load()"}),
        ("tool_result", "python", None),
        ("tool_call", "python", {"code": "df = clean(df)"}),
        ("tool_result", "python", None),
        ("file_change", None, None),
        ("tool_call", "python", {"code": "res = stats(df)"}),
        ("tool_result", "python", None),
        ("agent_message", None, None),
    ]
    for i, (etype, tool, args) in enumerate(spec):
        evs.append(
            Event(
                event_id=f"ev-{i+1:03d}",
                trajectory_id="run-001",
                event_type=etype,
                event_time=float(i),
                tool_name=tool,
                tool_args=args,
                tool_observation="ok" if etype == "tool_result" else None,
                visible_agent_context="assistant text" if etype == "agent_message" else None,
                token_usage={"prompt": 10, "completion": 5} if etype in ("tool_call", "agent_message") else {},
            )
        )
    return Trajectory(meta=golden_meta, events=evs)


@pytest.fixture()
def checker_samples() -> list:
    """20 labeled outputs for a checker whose AUROC should be 1.0:
    all positives score above all negatives."""
    samples = []
    for i in range(10):
        samples.append((0.9 - 0.01 * i, 1))   # correct outputs, scores 0.9..0.81
    for i in range(10):
        samples.append((0.1 + 0.01 * i, 0))   # incorrect outputs, scores 0.1..0.19
    return samples


@pytest.fixture()
def replacement_records() -> list:
    """3 tasks x paired arms; per-task deltas: t1: 1.0-0.0=1, t2: 0.5-0.5=0,
    t3: 0.0-1.0=-1 -> point estimate 0.0."""
    return [
        {"task_id": "t1", "arm": "control", "success": True},
        {"task_id": "t1", "arm": "treatment", "success": False},
        {"task_id": "t2", "arm": "control", "success": True},
        {"task_id": "t2", "arm": "control", "success": False},
        {"task_id": "t2", "arm": "treatment", "success": True},
        {"task_id": "t2", "arm": "treatment", "success": False},
        {"task_id": "t3", "arm": "control", "success": False},
        {"task_id": "t3", "arm": "treatment", "success": True},
        # t4 has only treatment -> excluded
        {"task_id": "t4", "arm": "treatment", "success": True},
    ]
