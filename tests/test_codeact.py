"""CodeAct-lite loop tests with a scripted fake client (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from verifront.agents.codeact import (
    CodeActAgent,
    CodeActConfig,
    TaskSpec,
    parse_action,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class FakeClient:
    """Scripted chat client; records calls for assertions."""

    model = "fake-model"
    snapshot = "fake-snapshot"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, temperature=0.0, max_tokens=1024, seed=None):
        self.calls.append({"n_messages": len(messages), "temperature": temperature,
                           "max_tokens": max_tokens, "seed": seed})
        return {
            "content": self.responses.pop(0),
            "token_usage": {"prompt": 10, "completion": 4},
            "model": self.model,
            "latency_s": 0.01,
            "raw": {},
        }


@pytest.fixture()
def task(tmp_path):
    return TaskSpec(task_id="t-demo", description="Compute 6*7 and print it.")


def test_parse_action_prefers_final_and_last_block():
    text = "<code>a=1</code> then <code>a=2</code> done <final>42</final>"
    assert parse_action(text) == ("final", "42")
    assert parse_action("<code>one</code>") == ("code", "one")
    assert parse_action("<code>first</code><code>second</code>") == ("code", "second")
    assert parse_action("no blocks here")[0] == "none"


def test_code_then_final_roundtrip(tmp_path, task):
    client = FakeClient([
        "<code>print('hello-from-code')</code>",
        "<final>The answer is 42</final>",
    ])
    cfg = CodeActConfig(max_steps=3, step_timeout_s=10, python_bin=sys.executable)
    agent = CodeActAgent(client, cfg, workdir=tmp_path / "run", agent_commit="test-commit")
    result = agent.run(task)

    assert result.status == "completed"
    assert result.final_answer == "The answer is 42"
    assert result.token_usage == {"prompt": 20, "completion": 8}
    # second call saw the observation of the first code run
    assert len(client.calls) == 2
    assert client.calls[1]["n_messages"] == 4  # system+user+assistant+observation
    assert result.steps[0]["exec_status"] == "ok"
    # trajectory validates cleanly
    errs = result.trajectory.validate()
    assert errs == [], errs
    kinds = [e.event_type for e in result.trajectory.events]
    assert kinds == ["agent_message", "tool_call", "tool_result", "agent_message"]
    # workspace kept the executed script
    assert (tmp_path / "run" / "step_01.py").exists()


def test_observation_content_reaches_next_prompt(tmp_path, task):
    client = FakeClient([
        "<code>print('marker-123')</code>",
        "<final>done</final>",
    ])
    cfg = CodeActConfig(max_steps=2, step_timeout_s=10, python_bin=sys.executable)
    agent = CodeActAgent(client, cfg, workdir=tmp_path)
    agent.run(task)
    # find the observation message sent on the second call
    # (FakeClient only stores counts, so re-run with a recording client)
    class RecordingClient(FakeClient):
        def chat(self, messages, **kw):
            self.last_messages = messages
            return super().chat(messages, **kw)

    rc = RecordingClient([
        "<code>print('marker-123')</code>",
        "<final>done</final>",
    ])
    CodeActAgent(rc, cfg, workdir=tmp_path / "r2").run(task)
    obs_msg = rc.last_messages[-1]["content"]
    assert "marker-123" in obs_msg
    assert obs_msg.startswith("EXECUTION RESULT [ok]")


def test_failing_code_reports_error_and_continues(tmp_path, task):
    client = FakeClient([
        "<code>raise SystemExit(3)</code>",
        "<final>recovered</final>",
    ])
    cfg = CodeActConfig(max_steps=2, step_timeout_s=10, python_bin=sys.executable)
    agent = CodeActAgent(client, cfg, workdir=tmp_path)
    result = agent.run(task)
    assert result.status == "completed"
    assert result.steps[0]["exec_status"] == "error"
    assert result.steps[0]["exit_code"] == 3


def test_timeout_observation(tmp_path, task):
    client = FakeClient([
        "<code>import time; time.sleep(5)</code>",
        "<final>gave up on that step</final>",
    ])
    cfg = CodeActConfig(max_steps=2, step_timeout_s=1.0, python_bin=sys.executable)
    agent = CodeActAgent(client, cfg, workdir=tmp_path)
    result = agent.run(task)
    assert result.steps[0]["exec_status"] == "timeout"


def test_format_error_then_final(tmp_path, task):
    client = FakeClient(["I will just talk, no block.", "<final>ok now</final>"])
    cfg = CodeActConfig(max_steps=2, step_timeout_s=10, python_bin=sys.executable)
    agent = CodeActAgent(client, cfg, workdir=tmp_path)
    result = agent.run(task)
    assert result.status == "completed"
    assert result.steps[0]["kind"] == "final"  # loop recorded the finished step
    # trajectory contains the format-error turn
    extras = [e.extra.get("parsed_action") for e in result.trajectory.events
              if e.event_type == "agent_message"]
    assert extras[0] == "none"


def test_budget_exhausted(tmp_path, task):
    client = FakeClient(["<code>pass</code>"] * 5)
    cfg = CodeActConfig(max_steps=4, step_timeout_s=5, python_bin=sys.executable)
    agent = CodeActAgent(client, cfg, workdir=tmp_path)
    result = agent.run(task)
    assert result.status == "budget_exhausted"
    assert result.final_answer is None
    assert len(result.steps) == 4
