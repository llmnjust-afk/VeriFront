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
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..agents.base import load_models_config
from ..agents.codeact import CodeActAgent, CodeActConfig, TaskSpec

_EVAL_LINE_RE = re.compile(r"^\((?P<success>\d)\s*,\s*(?P<detail>.*)\)\s*$")

# Directories that must NEVER be visible to the agent (official SAB gives agents
# only the dataset tree; eval/gold/rubrics enter the workdir at eval time only).
_AGENT_HIDDEN = ("gold_programs", "eval_programs", "scoring_rubrics")


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
    """Create workdir with a SANITIZED agent view + empty pred_results.

    Agent view: benchmark/ is a real directory whose only entry is a symlink
    `datasets` -> <benchmark_root>/benchmark/datasets. gold_programs /
    eval_programs / scoring_rubrics are invisible while the agent works
    (official SAB layout). run_eval() swaps in the full tree at eval time.
    """
    wd = paths.workdir
    wd.mkdir(parents=True, exist_ok=True)
    datasets_src = paths.benchmark_link_target() / "datasets"
    if not datasets_src.is_dir():
        raise FileNotFoundError(f"benchmark datasets missing: {datasets_src}")
    staged = wd / "benchmark"
    if staged.is_symlink() or staged.exists():
        if staged.is_symlink() and not staged.exists():
            staged.unlink()
        elif staged.is_dir() and not staged.is_symlink():
            shutil.rmtree(staged)
        else:
            raise FileExistsError(f"{staged} exists and is not a directory")
    staged.mkdir()
    os.symlink(datasets_src, staged / "datasets")
    _assert_agent_view_clean(staged)
    (wd / "pred_results").mkdir(exist_ok=True)


def _assert_agent_view_clean(staged: Path) -> None:
    names = {p.name for p in staged.iterdir()}
    leaked = names.intersection(_AGENT_HIDDEN)
    if leaked:
        raise RuntimeError(f"agent view leaks protected dirs: {sorted(leaked)}")


def _ensure_full_benchmark(paths: SabTaskPaths) -> None:
    """Swap the sanitized agent view for the full benchmark tree (eval time)."""
    staged = paths.workdir / "benchmark"
    target = paths.benchmark_link_target()
    if staged.is_symlink() and staged.resolve() == target.resolve():
        return
    if staged.is_symlink() or not staged.exists():
        staged.unlink(missing_ok=True)
    else:
        shutil.rmtree(staged)
    os.symlink(target, staged)


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
    _ensure_full_benchmark(paths)
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
    if parsed_success is None and proc.returncode != 0:
        parsed_success, detail = 0, "eval_crash (no verdict line; see stdout/stderr tails)"
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
