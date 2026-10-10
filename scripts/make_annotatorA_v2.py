#!/usr/bin/env python3
"""Annotator A, round 2 (handbook v2, semi-blind): re-labels the same 60 steps
with run_outcome / execution status / observation digest as input."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IN = REPO / "reports" / "annotation" / "annotation_sample.jsonl"
OUT = REPO / "reports" / "annotation" / "annotatorA_v2.jsonl"

# sample_idx -> (step_type, role_in_outcome, rationale)
A2 = {
 1: ("fix_rerun", "critical_success", "repairs step_09 indent error and produces correct CFT JSON"),
 2: ("data_inspection", "neutral", "module discovery (routine)"),
 3: ("data_inspection", "critical_success", "establishes truth=MFA semantics for the run"),
 4: ("data_inspection", "critical_success", "confirms split boundaries used by grouped design"),
 5: ("compute_run", "critical_success", "executes encoding+evaluation, writes accuracies.csv"),
 6: ("data_inspection", "neutral", "source regex sweep (routine)"),
 7: ("compute_run", "neutral", "intent was compute+write but IndentationError; repaired in step_10"),
 8: ("compute_run", "critical_success", "executes raster reclassification and writes outputs"),
 9: ("data_inspection", "critical_success", "onset source read underpins correct onset_hr"),
10: ("compute_run", "critical_success", "single-step score computation and JSON write"),
11: ("data_inspection", "neutral", "index overview"),
12: ("data_inspection", "neutral", "csv schemas and rule snippets"),
13: ("compute_run", "neutral", "errored (exit 1); repaired later in same successful run"),
14: ("data_inspection", "neutral", "source listing (routine)"),
15: ("data_inspection", "neutral", "prints rule files"),
16: ("data_inspection", "critical_success", "truth uniqueness and figure-encoding derivation"),
17: ("method_design", "critical_success", "defines Morgan features and grid for this run"),
18: ("method_design", "critical_success", "implements encoders plus MFA statistics"),
19: ("data_inspection", "neutral", "line-numbered sources (routine)"),
20: ("data_inspection", "neutral", "AST walk of rules"),
21: ("data_inspection", "neutral", "accuracy summary and sources"),
22: ("data_inspection", "neutral", "listing and schemas"),
23: ("data_inspection", "neutral", "module/version discovery (routine)"),
24: ("data_inspection", "neutral", "accuracy matrix dump"),
25: ("data_inspection", "critical_success", "six CFT method sources read"),
26: ("data_inspection", "neutral", "ccobra member inventory"),
27: ("compute_run", "critical_success", "executes featurization+GridSearchCV producing deliverable"),
28: ("compute_run", "critical_success", "PSS scoring and CSV in one execution"),
29: ("data_inspection", "critical_success", "confirms MultiIndex grouping structure"),
30: ("compute_run", "critical_success", "computes features and writes saliva_pred.json"),
31: ("data_inspection", "neutral", "environment/data sanity"),
32: ("compute_run", "neutral", "re-derives same correct result already established"),
33: ("data_inspection", "neutral", "source read (routine)"),
34: ("data_inspection", "neutral", "MFA table duplicates earlier derivation"),
35: ("compute_run", "critical_failure", "wrong token order/combination persisted to final csv"),
36: ("data_inspection", "neutral", "pipeline sources"),
37: ("compute_run", "critical_failure", "executes pre-clean + split-hrv pipeline producing wrong features"),
38: ("compute_run", "critical_failure", "re-runs pipeline and persists wrong endpoints"),
39: ("data_inspection", "neutral", "signatures and quantiles"),
40: ("data_inspection", "neutral", "listing and package checks"),
41: ("data_inspection", "neutral", "order/similarity exploration"),
42: ("data_inspection", "neutral", "flatten-order hypothesis comparison"),
43: ("compute_run", "critical_failure", "sum-combination persisted to final csv"),
44: ("data_inspection", "neutral", "signatures/docs and cadence stats"),
45: ("compute_run", "critical_failure", "order x weighting experiment locks wrong choice"),
46: ("compute_run", "critical_failure", "StratifiedKFold sweep contradicts grouped gold CV"),
47: ("compute_run", "critical_failure", "Otsu+RF executed, deviates from gold binarization"),
48: ("compute_run", "critical_failure", "pipeline run persists boundary-wrong endpoints"),
49: ("compute_run", "critical_failure", "clean+split hrv execution persists 57/91 features"),
50: ("compute_run", "critical_failure", "hand-rolled RRV executed; output violates eval contract"),
51: ("compute_run", "critical_failure", "Otsu+pipeline executed (second run)"),
52: ("data_inspection", "neutral", "walk and pickle overview; step itself errored"),
53: ("compute_run", "critical_failure", "hand-rolled RRV executed (second run)"),
54: ("data_inspection", "neutral", "walk and describe"),
55: ("data_inspection", "neutral", "raw dumps and Ragni summary"),
56: ("data_inspection", "neutral", "focused inspection (failed run)"),
57: ("data_inspection", "neutral", "alignment/nonfinite checks"),
58: ("compute_run", "neutral", "timed out at 300s; repaired later, not decisive"),
59: ("compute_run", "critical_success", "full search run lands F1 above threshold"),
60: ("data_inspection", "neutral", "listing and rule excerpts"),
}

def main() -> None:
    rows = [json.loads(l) for l in IN.open()]
    with OUT.open("w") as f:
        for r in rows:
            st, role, rat = A2[r["sample_idx"]]
            f.write(json.dumps({
                "i": r["sample_idx"], "task_id": r["task_id"], "stratum": r["stratum"],
                "run_outcome": r["run_outcome"], "step_idx": r["step_idx"],
                "step_type": st, "role_in_outcome": role, "rationale": rat,
            }) + "\n")
    from collections import Counter
    print("step_type:", dict(Counter(v[0] for v in A2.values())))
    print("role:", dict(Counter(v[1] for v in A2.values())))
    print("wrote", OUT)

if __name__ == "__main__":
    main()
