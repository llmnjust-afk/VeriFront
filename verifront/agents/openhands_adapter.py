"""Best-effort mapping of OpenHands event streams into the VeriFront Event schema.

OpenHands field names and event kinds vary across versions (the benchmarks repo
is mid V0->V1 migration, Prompt_V2 §2.1), so this adapter is deliberately
tolerant: unrecognized events are kept with event_type="other" and the original
payload in `extra`. P0 must pin the OpenHands commit and re-verify field
mapping against a real trajectory before any experiment uses it.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..traces.schema import Event, RunMeta, Trajectory

_TOOL_ACTIONS = {"run", "execute", "call_tool", "browse", "edit", "write", "read", "ipython"}


def map_openhands_events(raw_events: List[Dict[str, Any]], meta: RunMeta) -> Trajectory:
    events: List[Event] = []
    idx = 0
    for i, raw in enumerate(raw_events):
        action = raw.get("action")
        observation = raw.get("observation")
        if action:
            etype = "tool_call" if str(action).lower() in _TOOL_ACTIONS else "agent_message"
            tool_name = str(action)
            tool_args = raw.get("args") if isinstance(raw.get("args"), dict) else None
        elif observation is not None:
            etype = "tool_result"
            tool_name = str(raw.get("tool_name") or "")
            tool_args = None
        else:
            etype = "other"
            tool_name = ""
            tool_args = None
        idx += 1
        events.append(
            Event(
                event_id=f"ev-{idx:05d}",
                trajectory_id=meta.run_id,
                event_type=etype,
                event_time=float(raw.get("timestamp", i)) if raw.get("timestamp") is not None else float(i),
                tool_name=tool_name,
                tool_args=tool_args,
                tool_observation=observation if isinstance(observation, str) else None,
                visible_agent_context=raw.get("message") if isinstance(raw.get("message"), str) else None,
                extra={"openhands_raw_action": action, "openhands_index": i},
            )
        )
    return Trajectory(meta=meta, events=events)
