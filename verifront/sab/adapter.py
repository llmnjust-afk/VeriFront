"""SAB (ScienceAgentBench) adapter: benchmark facts in, VeriFront runs out.

Responsibilities (P0):
- map instance_id -> task metadata from the verified parquet;
- prepare a per-task work directory that mirrors the layout SAB eval scripts
  expect (cwd contains ./pred_results/ and ./benchmark/ -> benchmark root);
- build the TaskSpec exactly from what SAB gives agents (task_inst +
  domain_knowledge + dataset tree/preview) — gold programs are NEVER shown;
- run the official eval script after the agent finishes and parse its
  "(success, detail)" output.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..agents.base import load_models_config
from ..agents.codeact import CodeActAgent, CodeActConfig, TaskSpec

_EVAL_LINE_RE = re.compile(r"^\((?P<success>\d)\s*,\s*(?P<detail>.*)\)\s*$")


@dataclass
class SabTaskPaths:
    benchmark_root: Path  # dir that CONTAINS benchmark/ (i.e. benchmark_verified/)
    workdir: Path

    def benchmark_link_target(self) -> Path:
        return self.benchmark_root / "benchmark"


def load_verified_tasks(parquet_path):
    import pandas as pd

    return pd.read_parquet(parquet_path)


def get_task(df, instance_id: int):
    rows = df[df["instance_id"] == instance_id]
    if len(rows) != 1:
        raise ValueError(f"instance_id {instance_id}: expected 1 row, got {len(rows)}")
    return rows.iloc[0]


def prepare_workdir(paths: SabTaskPaths) -> None:
    """Create workdir with benchmark symlink + empty pred_results (SAB eval cwd)."""
    wd = paths.workdir
    wd.mkdir(parents=True, exist_ok=True)
    link = wd / "benchmark"
    target = paths.benchmark_link_target()
    if not target.is_dir():
        raise FileNotFoundError(f"benchmark dir missing: {target}")
    if link.is_symlink() or link.exists():
        if not link.is_symlink():
            raise FileExistsError(f"{link} exists and is not a symlink")
    else:
        os.symlink(target, link)
    (wd / "pred_results").mkdir(exist_ok=True)


def build_task_spec(row, instance_id: int, extra_rules: str = "") -> TaskSpec:
    inst = str(row["task_inst"]).strip()
    dk = str(row["domain_knowledge"] or "").strip()
    tree = str(row["dataset_folder_tree"] or "").strip()
    preview = str(row["dataset_preview"] or "").strip()
    output = str(row["output_fname"] or "").strip()
    description = (
        f"{inst}\n\n"
        f"Required output file (exact path, relative to the working directory):\n{output}\n\n"
        f"Dataset folder tree:\n{tree}\n\n"
        f"Dataset preview:\n{preview}\n"
    )
    if dk and dk.lower() != "nan":
        description += f"\nDomain knowledge provided by the benchmark:\n{dk}\n"
    if extra_rules:
        description += f"\n{extra_rules}\n"
    return TaskSpec(task_id=f"sab-{instance_id}", description=description)


def run_codeact(paths: SabTaskPaths, spec: TaskSpec, client, config: CodeActConfig,
                agent_commit: str = "", benchmark_version: str = "sab-verified-c26e151"):
    agent = CodeActAgent(client, config, workdir=paths.workdir,
                         agent_commit=agent_commit, benchmark_version=benchmark_version)
    return agent.run(spec)


def parse_eval_line(line: str):
    m = _EVAL_LINE_RE.match(line.strip())
    if m:
        return int(m.group("success")), m.group("detail").strip().strip("'\"")
    return None


def run_eval(paths: SabTaskPaths, eval_script_name: str, python_bin: str,
             timeout_s: float = 600.0):
    """Run the official eval script with cwd=workdir; parse (success, detail)."""
    script = paths.benchmark_link_target() / "eval_programs" / eval_script_name
    if not script.is_file():
        raise FileNotFoundError(script)
    proc = subprocess.run(
        [python_bin, str(script)],
        cwd=str(paths.workdir),
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    parsed_success, detail = None, ""
    for line in proc.stdout.splitlines():
        parsed = parse_eval_line(line)
        if parsed:
            parsed_success, detail = parsed
            break
    return {
        "success": parsed_success,
        "detail": detail,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def client_from_models_config(cfg_path, arm: str):
    """Reuse the codeact factory; kept here for import convenience in scripts."""
    from ..agents.codeact import client_from_config

    return client_from_config(cfg_path, arm)
