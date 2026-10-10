"""Deterministic prefix replay for counterfactual replacement points.

Implements docs/design_counterfactual.md §3 (Prompt_V2 §4 scheme A):
- message layer: rebuilt BYTE-EXACT from the parent trace (system template,
  agent_message context, EXECUTION RESULT observations, incl. errors);
- filesystem layer: the parent's saved step scripts are re-executed in a fresh
  sandbox workdir with the same interpreter and dataset view.
Fidelity = file manifest diff + per-step observation agreement, recorded for
the acceptance gate (>=90% recoverable points in the pilot).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from verifront.agents.codeact import (FORMAT_ERROR_OBSERVATION,
                                      SYSTEM_PROMPT_TEMPLATE, CodeActAgent,
                                      CodeActConfig, TaskSpec)


def load_run_events(run_dir: Path) -> List[Dict[str, Any]]:
    events = []
    for line in (run_dir / "trace.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        if "_meta" in ev:
            continue
        events.append(ev)
    return events


def extract_generated_steps(run_dir: Path) -> List[Dict[str, Any]]:
    """One record per generated step (message turn), in order."""
    events = load_run_events(run_dir)
    steps: List[Dict[str, Any]] = []
    pending_script: Optional[str] = None
    for ev in events:
        et = ev.get("event_type")
        if et == "agent_message":
            steps.append({
                "step_no": len(steps) + 1,
                "content": ev.get("visible_agent_context") or "",
                "parsed": (ev.get("extra") or {}).get("parsed_action"),
                "script": None, "observation": None, "exec_status": None,
            })
        elif et == "tool_call":
            pending_script = (ev.get("tool_args") or {}).get("script")
        elif et == "tool_result":
            if steps and steps[-1]["script"] is None:
                steps[-1]["script"] = pending_script
                steps[-1]["observation"] = ev.get("tool_observation") or ""
                steps[-1]["exec_status"] = ev.get("execution_status") or ""
            pending_script = None
    return steps


def rebuild_messages(task: TaskSpec, config: CodeActConfig,
                     steps: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Rebuild the assistant-visible history for the first `len(steps)` turns,
    byte-identical to what CodeActAgent.run produced in the parent run."""
    system = SYSTEM_PROMPT_TEMPLATE.format(
        max_steps=config.max_steps,
        task_description=task.description,
        extra_context=(task.extra_context or ""),
    )
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Begin. Output your first block."},
    ]
    for s in steps:
        messages.append({"role": "assistant", "content": s["content"]})
        if s["parsed"] == "final":
            break  # final turn has no execution observation
        if s["exec_status"] is None:  # format_error turn
            observation = FORMAT_ERROR_OBSERVATION
            status = "format_error"
        else:
            observation = s["observation"]
            status = s["exec_status"]
        messages.append({"role": "user",
                         "content": f"EXECUTION RESULT [{status}]\n{observation}"})
    return messages


def file_manifest(workdir: Path) -> Dict[str, str]:
    """SHA256 of every file under workdir except this-run step scripts."""
    out: Dict[str, str] = {}
    for p in sorted(workdir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(workdir).as_posix()
        if rel.startswith("step_") and rel.endswith(".py"):
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        out[rel] = h
    return out


def replay_prefix(run_dir: Path, agent: CodeActAgent,
                  upto_exclusive: int) -> Dict[str, Any]:
    """Re-execute the parent's saved step scripts 1..upto_exclusive-1 in the
    agent's (fresh, prepared) workdir. Scripts come from the parent run's
    artifact directory (they are copied into the workdir before execution).
    Returns fidelity records."""
    steps = extract_generated_steps(run_dir)
    prefix = [s for s in steps if s["step_no"] < upto_exclusive and s["script"]]
    per_step = []
    for s in prefix:
        src = run_dir / s["script"]
        script = agent.workdir / s["script"]
        if not src.is_file():
            per_step.append({"step_no": s["step_no"], "script": s["script"],
                             "error": "missing_script"})
            continue
        script.write_text(src.read_text(), encoding="utf-8")
        out = agent._execute(script)
        obs_orig = s["observation"] or ""
        obs_replay = out["observation"]
        per_step.append({
            "step_no": s["step_no"], "script": s["script"],
            "orig_status": s["exec_status"], "replay_status": out["status"],
            "obs_identical": obs_orig == obs_replay,
            "obs_diff_chars": _diff_chars(obs_orig, obs_replay),
        })
        if obs_orig != obs_replay:
            per_step[-1]["obs_diff_excerpt"] = _diff_excerpt(obs_orig, obs_replay)
    return {"steps": per_step,
            "manifest": file_manifest(agent.workdir),
            "all_status_match": all(p.get("orig_status") == p.get("replay_status")
                                    for p in per_step),
            "n_obs_identical": sum(1 for p in per_step if p.get("obs_identical")),
            "n_replayed": len(per_step)}


def _diff_chars(a: str, b: str) -> int:
    import difflib
    sm = difflib.SequenceMatcher(None, a, b)
    return int((1 - sm.ratio()) * max(len(a), len(b)))


def _diff_excerpt(a: str, b: str, max_chars: int = 300) -> str:
    import difflib
    d = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))
    text = "\n".join(d)
    return text[:max_chars]
