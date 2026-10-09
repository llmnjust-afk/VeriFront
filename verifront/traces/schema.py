"""Minimal trajectory log format (Prompt_V2 §3.4).

Run-level metadata lives in RunMeta; per-event fields in Event. Anything not in
the minimal schema goes into Event.extra so the log stays lossy-free while the
required contract stays enforceable. Large artifacts are stored OUT of band and
referenced by SHA-256 (file_artifact_hashes).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

RUN_REQUIRED_FIELDS = [
    "run_id",
    "task_id",
    "benchmark_version",
    "agent_commit",
    "model_id",
    "model_snapshot_or_revision",
    "sampling_config",
    "environment_digest",
]

EVENT_REQUIRED_FIELDS = [
    "event_id",
    "trajectory_id",
    "event_type",
    "event_time",
]

KNOWN_EVENT_TYPES = {
    "agent_message",
    "tool_call",
    "tool_result",
    "file_change",
    "environment_change",
    "other",
}


@dataclass
class RunMeta:
    run_id: str
    task_id: str
    benchmark_version: str
    agent_commit: str
    model_id: str
    model_snapshot_or_revision: str
    sampling_config: Dict[str, Any] = field(default_factory=dict)
    environment_digest: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors = []
        for k in RUN_REQUIRED_FIELDS:
            v = getattr(self, k, None)
            if v is None or (isinstance(v, str) and not v.strip()):
                errors.append(f"RunMeta missing required field: {k}")
        return errors


@dataclass
class Event:
    event_id: str
    trajectory_id: str
    event_type: str
    event_time: float
    action_id: Optional[str] = None
    scientific_step_id: Optional[str] = None
    step_type: Optional[str] = None
    visible_agent_context: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_observation: Optional[str] = None
    file_artifact_hashes: Dict[str, str] = field(default_factory=dict)
    execution_status: Optional[str] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    latency: Optional[float] = None
    api_cost: Optional[float] = None
    evaluation_version: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors = []
        for k in EVENT_REQUIRED_FIELDS:
            v = getattr(self, k, None)
            if v is None or (isinstance(v, str) and not v.strip()):
                errors.append(f"{self.event_id or '?'}: missing required field {k}")
        if self.event_type not in KNOWN_EVENT_TYPES:
            errors.append(f"{self.event_id}: unknown event_type {self.event_type!r}")
        return errors


@dataclass
class Trajectory:
    meta: RunMeta
    events: List[Event] = field(default_factory=list)

    def append(self, event: Event) -> None:
        self.events.append(event)

    def validate(self) -> List[str]:
        errors = list(self.meta.validate())
        seen = set()
        prev_time = None
        for ev in self.events:
            errors.extend(ev.validate())
            if ev.event_id in seen:
                errors.append(f"duplicate event_id {ev.event_id}")
            seen.add(ev.event_id)
            if prev_time is not None and ev.event_time < prev_time:
                errors.append(f"{ev.event_id}: event_time not monotonic")
            prev_time = ev.event_time
        return errors

    def to_jsonl(self) -> str:
        lines = [json.dumps({"_meta": asdict(self.meta)}, ensure_ascii=False)]
        for ev in self.events:
            lines.append(json.dumps(asdict(ev), ensure_ascii=False))
        return "\n".join(lines) + "\n"

    @classmethod
    def from_jsonl(cls, text: str) -> "Trajectory":
        meta = None
        events: List[Event] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if "_meta" in rec:
                meta = RunMeta(**rec["_meta"])
            else:
                events.append(Event(**rec))
        if meta is None:
            raise ValueError("trajectory jsonl missing _meta line")
        return cls(meta=meta, events=events)


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
