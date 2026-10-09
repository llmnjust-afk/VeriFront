"""CodeAct-lite: VeriFront's minimal execution loop (chosen after the OpenHands
infeasibility decision, see docs/protocol_pilot.md §6).

Design (Prompt_V2 §5.3 + §8 deviation log):
- the model alternates between ONE action per turn: a standalone Python script
  (<code> block) or the final answer (<final> block);
- scripts run in a fresh subprocess with the task's interpreter (the SAB task
  conda env), inside a per-run workspace; no shell interpolation anywhere;
- every turn is recorded as schema-compliant events so the three-layer
  trajectory representation is built natively, not post-hoc;
- budgets (steps, per-exec timeout, total wall time) are explicit config, part
  of the continuation spec hashing story in counterfactual runs.

The API key travels only through the client; it is never logged or persisted.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import load_models_config
from .openai_compat import OpenAICompatClient
from ..traces.schema import Event, RunMeta, Trajectory, sha256_bytes

_CODE_RE = re.compile(r"<code>(.*?)</code>", re.DOTALL)
_FINAL_RE = re.compile(r"<final>(.*?)</final>", re.DOTALL)

SYSTEM_PROMPT_TEMPLATE = """You are a careful scientific Python coder solving a research-computing task.

Work turn by turn. On EVERY turn output EXACTLY ONE block and nothing else:

<code>
# a complete, standalone Python script that makes one round of progress
</code>

or, when the task is fully done:

<final>
# the final answer: what was produced, key numbers, and where results are saved
</final>

Rules:
- Each <code> block is executed in a fresh Python process inside your working
  directory; files you write there persist between turns.
- Print the intermediate results you need to observe; you cannot inspect
  anything silently.
- No interactive input, no network access, no installs beyond the provided
  environment. Stay within the task's stated requirements.
- Prefer finishing properly over stopping early; you have at most {max_steps} turns.

Task description:
{task_description}
{extra_context}"""

FORMAT_ERROR_OBSERVATION = (
    "FORMAT ERROR: no <code> or <final> block found. "
    "Respond with EXACTLY ONE <code>...</code> or <final>...</final> block."
)


@dataclass
class TaskSpec:
    task_id: str
    description: str
    extra_context: str = ""  # e.g. data dictionary / file inventory (text only)


@dataclass
class CodeActConfig:
    max_steps: int = 6
    step_timeout_s: float = 300.0
    total_wall_s: float = 1800.0
    max_tokens: int = 8192  # reasoning models spend this budget on thinking + code
    temperature: float = 0.0
    seed: Optional[int] = None
    obs_char_limit: int = 4000
    python_bin: str = "python3"  # per-run task interpreter (SAB task env)


@dataclass
class RunResult:
    status: str  # completed | budget_exhausted | api_error | wallclock_exceeded
    final_answer: Optional[str]
    token_usage: Dict[str, int]
    wall_s: float
    steps: List[Dict[str, Any]] = field(default_factory=list)
    trajectory: Optional[Trajectory] = None


def parse_action(text: str):
    """Return ("final", content) | ("code", content) | ("none", text).

    <final> wins if both appear; within a kind the LAST block wins so that
    self-corrections override earlier drafts.
    """
    finals = _FINAL_RE.findall(text)
    if finals:
        return "final", finals[-1].strip()
    codes = _CODE_RE.findall(text)
    if codes:
        return "code", codes[-1].strip()
    return "none", text.strip()


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n... [truncated {len(s) - limit} chars]"


class CodeActAgent:
    """Executes the CodeAct-lite loop and records a schema-valid trajectory."""

    def __init__(self, client, config: CodeActConfig, workdir, agent_commit: str = "",
                 benchmark_version: str = "sab-pilot-p0"):
        self.client = client
        self.config = config
        self.workdir = Path(workdir)
        self.agent_commit = agent_commit
        self.benchmark_version = benchmark_version

    def _new_event(self, traj_id: str, i: int, etype: str, **kw) -> Event:
        return Event(
            event_id=f"{traj_id}-ev-{i:03d}",
            trajectory_id=traj_id,
            event_type=etype,
            event_time=time.time(),
            **kw,
        )

    def run(self, task: TaskSpec) -> RunResult:
        self.workdir.mkdir(parents=True, exist_ok=True)
        traj_id = f"{task.task_id}-{int(time.time())}"
        meta = RunMeta(
            run_id=traj_id,
            task_id=task.task_id,
            benchmark_version=self.benchmark_version,
            agent_commit=self.agent_commit,
            model_id=getattr(self.client, "model", "unknown"),
            model_snapshot_or_revision=getattr(self.client, "snapshot", "") or "",
            sampling_config={
                "temperature": self.config.temperature,
                "seed": self.config.seed,
                "max_tokens": self.config.max_tokens,
                "max_steps": self.config.max_steps,
                "step_timeout_s": self.config.step_timeout_s,
            },
            environment_digest={"python_bin": self.config.python_bin},
        )
        traj = Trajectory(meta=meta)
        system = SYSTEM_PROMPT_TEMPLATE.format(
            max_steps=self.config.max_steps,
            task_description=task.description,
            extra_context=(task.extra_context or ""),
        )
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": "Begin. Output your first block."},
        ]
        totals = {"prompt": 0, "completion": 0}
        steps: List[Dict[str, Any]] = []
        status = "budget_exhausted"
        final_answer: Optional[str] = None
        start = time.monotonic()
        ev_i = 0

        for step_i in range(1, self.config.max_steps + 1):
            if time.monotonic() - start > self.config.total_wall_s:
                status = "wallclock_exceeded"
                break
            resp = self.client.chat(
                messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed,
            )
            u = resp["token_usage"]
            totals["prompt"] += u.get("prompt", 0)
            totals["completion"] += u.get("completion", 0)
            content = resp["content"] or ""
            kind, payload = parse_action(content)

            ev_i += 1
            traj.append(self._new_event(
                traj_id, ev_i, "agent_message",
                visible_agent_context=content,
                token_usage=dict(u),
                latency=resp.get("latency_s"),
                extra={"parsed_action": kind},
            ))

            if kind == "final":
                final_answer = payload
                status = "completed"
                steps.append({"step": step_i, "kind": "final"})
                break
            if kind == "none":
                observation = FORMAT_ERROR_OBSERVATION
                exec_status = "format_error"
            else:
                script = self.workdir / f"step_{step_i:02d}.py"
                script.write_text(payload, encoding="utf-8")
                ev_i += 1
                call_ev = self._new_event(
                    traj_id, ev_i, "tool_call",
                    action_id=f"act-{step_i:03d}",
                    tool_name="python",
                    tool_args={"script": script.name, "code_sha256": sha256_bytes(payload.encode("utf-8"))},
                )
                traj.append(call_ev)
                out = self._execute(script)
                ev_i += 1
                traj.append(self._new_event(
                    traj_id, ev_i, "tool_result",
                    action_id=f"act-{step_i:03d}",
                    tool_name="python",
                    tool_observation=out["observation"],
                    execution_status=out["status"],
                ))
                observation = out["observation"]
                exec_status = out["status"]
                steps.append({
                    "step": step_i, "kind": "code", "script": script.name,
                    "exit_code": out.get("exit_code"), "exec_status": exec_status,
                })

            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"EXECUTION RESULT [{exec_status}]\n{observation}"})

        result = RunResult(
            status=status,
            final_answer=final_answer,
            token_usage=totals,
            wall_s=round(time.monotonic() - start, 3),
            steps=steps,
            trajectory=traj,
        )
        return result

    def _execute(self, script: Path) -> Dict[str, Any]:
        try:
            proc = subprocess.run(
                [self.config.python_bin, str(script)],
                cwd=str(self.workdir),
                capture_output=True,
                text=True,
                timeout=self.config.step_timeout_s,
            )
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
            timed_out = False
        except subprocess.TimeoutExpired as e:
            stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
            stderr = (e.stderr or "") if isinstance(e.stderr, str) else ""
            code, timed_out = None, True
        if timed_out:
            status = "timeout"
        elif code == 0:
            status = "ok"
        else:
            status = "error"
        observation = (
            f"exit_code: {code}\n--- STDOUT ---\n{_truncate(stdout, self.config.obs_char_limit)}"
            f"\n--- STDERR ---\n{_truncate(stderr, self.config.obs_char_limit)}"
        )
        if timed_out:
            observation += f"\n[TIMEOUT after {self.config.step_timeout_s}s]"
        return {"observation": observation, "status": status, "exit_code": code}


def client_from_config(cfg_path, arm: str = "frontier") -> OpenAICompatClient:
    """Build the OpenAI-compatible client for an arm from configs/models.yaml.

    arm="frontier": uses cfg['frontier'] (base_url/model/snapshot + env key).
    arm="local:<name>": uses cfg['local'] entry with that name and its endpoint.
    The API key is read from the environment only.
    """
    cfg = load_models_config(cfg_path)
    if arm == "frontier":
        f = cfg["frontier"]
        client = OpenAICompatClient(
            base_url=os.environ.get(f.get("base_url_env") or "FRONTIER_BASE_URL", f.get("base_url") or ""),
            model=f["model_id"],
            api_key_env=f.get("api_key_env") or "FRONTIER_API_KEY",
        )
        client.snapshot = f.get("snapshot") or ""
        return client
    if arm.startswith("local:"):
        name = arm.split(":", 1)[1]
        entry = next((m for m in cfg.get("local") or [] if m.get("name") == name), None)
        if entry is None:
            raise ValueError(f"local model {name!r} not in models.yaml")
        client = OpenAICompatClient(
            base_url=entry["endpoint"],
            model=entry.get("model_id") or name,
            api_key_env=entry.get("api_key_env") or "LOCAL_MODEL_API_KEY",
        )
        client.snapshot = entry.get("hf_revision") or ""
        return client
    raise ValueError(f"unknown arm {arm!r}")
