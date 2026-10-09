"""Group events into actions and map actions onto scientific-semantic steps.

Grouping rule (registered here, not improvised per-run):
- a tool_call event OPENS an action; subsequent tool_result / file_change /
  environment_change events attach to it (matched by explicit action_id when
  present, else by adjacency);
- an agent_message event is its own action of kind "message";
- unknown ("other") events attach to the currently open action, else stand alone.

Step mapping must be provided EXPLICITLY (annotation artifact), and
validate_step_mapping enforces: contiguous non-overlapping action ranges,
known step types, and explicit 'unassigned' handling for leftovers.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

from .. import STEP_TYPES, UNASSIGNABLE
from .schema import Event

ALL_TYPES = STEP_TYPES + [UNASSIGNABLE]


@dataclass
class Action:
    action_id: str
    kind: str  # "tool" | "message" | "other"
    event_ids: List[str]
    tool_name: Optional[str] = None


@dataclass
class SemanticStep:
    step_id: str
    action_ids: List[str]  # contiguous range in trajectory order
    step_type: str
    notes: str = ""


def group_events_into_actions(events: List[Event]) -> List[Action]:
    actions: List[Action] = []
    open_action: Optional[Action] = None

    def close():
        nonlocal open_action
        open_action = None

    for i, ev in enumerate(events):
        aid = ev.action_id
        if ev.event_type == "tool_call":
            close()
            name = f"act-{i+1:05d}" if not aid else aid
            open_action = Action(action_id=name, kind="tool", event_ids=[ev.event_id], tool_name=ev.tool_name)
            actions.append(open_action)
        elif ev.event_type == "agent_message":
            close()
            name = f"act-{i+1:05d}" if not aid else aid
            open_action = Action(action_id=name, kind="message", event_ids=[ev.event_id])
            actions.append(open_action)
        else:
            if aid and open_action is not None and aid == open_action.action_id:
                open_action.event_ids.append(ev.event_id)
            elif aid and open_action is None:
                actions.append(Action(action_id=aid, kind="other", event_ids=[ev.event_id]))
            elif open_action is not None:
                open_action.event_ids.append(ev.event_id)
            else:
                actions.append(Action(action_id=f"act-{i+1:05d}", kind="other", event_ids=[ev.event_id]))
    return actions


def load_step_mapping(rows: List[Dict]) -> List[SemanticStep]:
    steps = []
    for r in rows:
        st = SemanticStep(
            step_id=str(r["step_id"]),
            action_ids=[str(a) for a in r["action_ids"]],
            step_type=str(r["step_type"]),
            notes=str(r.get("notes", "")),
        )
        if st.step_type not in ALL_TYPES:
            raise ValueError(f"unknown step_type {st.step_type!r} for {st.step_id}")
        steps.append(st)
    return steps


def validate_step_mapping(actions: List[Action], steps: List[SemanticStep]) -> List[str]:
    """Errors: overlaps, non-contiguous ranges, duplicate/unknown action ids."""
    errors: List[str] = []
    known = {a.action_id for a in actions}
    claimed: Dict[str, str] = {}
    for st in steps:
        ids = st.action_ids
        if not ids:
            errors.append(f"{st.step_id}: empty action range")
            continue
        for aid in ids:
            if aid not in known:
                errors.append(f"{st.step_id}: unknown action_id {aid!r}")
            if aid in claimed:
                errors.append(f"{st.step_id}: action {aid!r} already claimed by {claimed[aid]!r}")
            claimed[aid] = st.step_id
        # contiguity: positions in `actions` must be consecutive
        positions = [i for i, a in enumerate(actions) if a.action_id in ids]
        if len(positions) == len(ids) and positions != list(range(positions[0], positions[0] + len(ids))):
            errors.append(f"{st.step_id}: action range not contiguous: {ids}")
    # unassigned actions are allowed but must be reported by the caller
    return errors


def unassigned_actions(actions: List[Action], steps: List[SemanticStep]) -> List[str]:
    claimed = {aid for st in steps for aid in st.action_ids}
    return [a.action_id for a in actions if a.action_id not in claimed]


def coverage(steps: List[SemanticStep]) -> Counter:
    return Counter(st.step_type for st in steps)
