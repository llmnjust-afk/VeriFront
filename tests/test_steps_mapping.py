"""Event->Action grouping and SemanticStep mapping validation (§10.2)."""

import pytest

from verifront.traces.schema import Event
from verifront.traces.steps import (
    coverage,
    group_events_into_actions,
    load_step_mapping,
    unassigned_actions,
    validate_step_mapping,
)


def _ev(i, etype, tool=None, args=None, action_id=None):
    return Event(
        event_id=f"ev-{i:03d}",
        trajectory_id="t",
        event_type=etype,
        event_time=float(i),
        tool_name=tool,
        tool_args=args,
        action_id=action_id,
    )


def test_grouping_tool_call_and_result_merge(golden_trajectory):
    actions = group_events_into_actions(golden_trajectory.events)
    # 2 messages + 3 tool actions = 5 actions (results merge into their calls)
    assert len(actions) == 5
    kinds = [a.kind for a in actions]
    assert kinds == ["message", "tool", "tool", "tool", "message"]
    # first tool action contains the call AND its result
    assert len(actions[1].event_ids) == 2
    assert actions[1].tool_name == "python"


def test_valid_mapping_passes(golden_trajectory):
    actions = group_events_into_actions(golden_trajectory.events)
    steps = load_step_mapping(
        [
            {"step_id": "s1", "action_ids": [actions[0].action_id], "step_type": "analysis_planning"},
            {"step_id": "s2", "action_ids": [actions[1].action_id, actions[2].action_id], "step_type": "doc_parse_convert"},
            {"step_id": "s3", "action_ids": [actions[3].action_id], "step_type": "numeric_stats"},
            {"step_id": "s4", "action_ids": [actions[4].action_id], "step_type": "result_interpretation"},
        ]
    )
    assert validate_step_mapping(actions, steps) == []
    cov = coverage(steps)
    assert cov["doc_parse_convert"] == 1
    assert cov["numeric_stats"] == 1


def test_overlap_is_rejected(golden_trajectory):
    actions = group_events_into_actions(golden_trajectory.events)
    steps = load_step_mapping(
        [
            {"step_id": "s1", "action_ids": [actions[1].action_id], "step_type": "code_gen_repair"},
            {"step_id": "s2", "action_ids": [actions[1].action_id], "step_type": "numeric_stats"},
        ]
    )
    errs = validate_step_mapping(actions, steps)
    assert any("already claimed" in e for e in errs)


def test_non_contiguous_range_is_rejected(golden_trajectory):
    actions = group_events_into_actions(golden_trajectory.events)
    steps = load_step_mapping(
        [{"step_id": "s1", "action_ids": [actions[0].action_id, actions[4].action_id], "step_type": "analysis_planning"}]
    )
    errs = validate_step_mapping(actions, steps)
    assert any("not contiguous" in e for e in errs)


def test_unknown_action_or_type_is_rejected(golden_trajectory):
    actions = group_events_into_actions(golden_trajectory.events)
    with pytest.raises(ValueError):
        load_step_mapping([{"step_id": "s", "action_ids": ["a1"], "step_type": "not_a_type"}])
    steps = load_step_mapping([{"step_id": "s", "action_ids": ["ghost"], "step_type": "retrieval"}])
    assert any("unknown action_id" in e for e in validate_step_mapping(actions, steps))


def test_unassigned_actions_are_reported_not_hidden(golden_trajectory):
    actions = group_events_into_actions(golden_trajectory.events)
    steps = load_step_mapping([{"step_id": "s1", "action_ids": [actions[0].action_id], "step_type": "analysis_planning"}])
    un = unassigned_actions(actions, steps)
    assert len(un) == 4  # 4 actions deliberately left unassigned
