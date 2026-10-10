#!/usr/bin/env python3
"""Build the v2 B-side sheet: same 60 steps, now semi-blind (adds run outcome,
step execution status, observation digest per handbook v2 §5)."""
import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "runs"
OUT = REPO / "reports" / "annotation" / "annotation_B2_sheet.xlsx"

def clean(s: str, n: int = 400) -> str:
    return " | ".join(str(s).split())[:n]

rows = [json.loads(l) for l in (REPO / "reports" / "annotation" / "annotation_sample.jsonl").open()]
wb = Workbook()
ws = wb.active
ws.title = "annotation_B2"
header = ["sample_idx", "task_id", "step_idx", "run_outcome", "step_exec_status",
          "observation_digest", "code_step_python", "step_type_B2", "role_in_outcome_B2", "notes"]
ws.append(header)
for c in range(1, len(header) + 1):
    cell = ws.cell(row=1, column=c)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="4472C4")

miss = 0
for r in rows:
    run_dir = RUNS / f"sab_{r['task_id']}" / "frontier" / r["stamp"]
    trace = run_dir / "trace.jsonl"
    status, digest = "", ""
    if trace.is_file():
        target = r["step_idx"] + ".py"
        pending = None
        for line in trace.read_text().splitlines():
            ev = json.loads(line)
            if ev.get("event_type") == "tool_call":
                pending = (ev.get("tool_args") or {}).get("script")
            elif ev.get("event_type") == "tool_result" and pending == target:
                status = ev.get("execution_status") or ""
                obs = ev.get("tool_observation") or ""
                digest = clean(obs)
                break
    if not status:
        miss += 1
    code = r["code"]
    if len(code) > 32000:
        code = code[:32000] + "\n# ...TRUNCATED..."
    ws.append([r["sample_idx"], int(r["task_id"]), r["step_idx"], r["run_outcome"],
               status, digest, code, "", "", ""])
    row = ws.max_row
    for c in (6, 8):
        ws.cell(row=row, column=c).alignment = Alignment(wrap_text=True, vertical="top")

for col, w in zip("ABCDEFGHIJ", (11, 9, 11, 12, 13, 60, 100, 26, 24, 28)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "A2"

ins = wb.create_sheet("instructions_v2")
ins["A1"] = "B-side annotation ROUND 2 (handbook v2, semi-blind)"
ins["A1"].font = Font(bold=True, size=13)
lines = [
    "",
    "Same 60 steps as round 1. NEW columns give you the facts role labels need:",
    "  D) run_outcome        - success/failure of the WHOLE run this step belongs to",
    "  E) step_exec_status   - ok / error / timeout of THIS step's execution",
    "  F) observation_digest - first lines of what the step actually printed/raised",
    "",
    "Fill G) step_type_B2 and H) role_in_outcome_B2 for every row.",
    "  step_type_B2: data_inspection | data_prep | method_design | compute_run |",
    "                eval_check | fix_rerun | output_write | final_report",
    "  role_in_outcome_B2: critical_success | critical_failure | neutral",
    "",
    "v2 role definitions (handbook v2 §3):",
    "  critical_success: removing/weakening this step would plausibly flip the run",
    "    to failure (max 2 per successful run).",
    "  critical_failure: correcting this step in isolation would most plausibly flip",
    "    the failed run to success (max 2 per failed run).",
    "  neutral: routine progress; ALSO steps that errored but were fully repaired",
    "    later without changing the run's outcome.",
    "",
    "v2 type judgment rules: C1 compute-vs-write by dominant work; C2 eval_check is",
    "self-verification of your own code/results only (dataset semantics probing is",
    "data_inspection); C3 design+run in one script -> compute_run if heavy execution",
    "dominates; C4 errored steps get type by intent; C5 env probes are data_inspection.",
    "",
    "You are still blind to annotator A's labels.",
    "Save as annotation_B2_filled.xlsx and return it.",
]
for i, line in enumerate(lines, start=2):
    ins[f"A{i}"] = line
ins.column_dimensions["A"].width = 120

wb.save(OUT)
print("wrote", OUT, "| steps missing exec status:", miss)
