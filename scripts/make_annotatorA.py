#!/usr/bin/env python3
"""Annotator A (model-annotated, independent pass) for the 60-step trial set.

Labels follow docs/step_annotation_handbook.md v1: step_type in
{data_inspection, data_prep, method_design, compute_run, eval_check,
fix_rerun, output_write, final_report}; role_in_outcome in
{critical_success, critical_failure, neutral}.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IN = REPO / "reports" / "annotation" / "annotation_sample.jsonl"
OUT = REPO / "reports" / "annotation" / "annotatorA.jsonl"

# sample_idx -> (step_type, role_in_outcome, rationale)
A = {
 1: ("compute_run", "critical_success", "loads HR, runs CFT with standard structure, writes required JSON"),
 2: ("data_inspection", "critical_success", "locates CFT module and members - gateway to correct implementation"),
 3: ("data_inspection", "critical_success", "derives truth=MFA semantics from Ragni2016 vs existing truth map"),
 4: ("data_inspection", "critical_success", "verifies label blocks vs stated split boundaries for group-CV design"),
 5: ("method_design", "critical_success", "implements response/task encoding, hit credit, NVC rule logic"),
 6: ("data_inspection", "critical_success", "regex sweep of CFT source; all defs enumerated"),
 7: ("compute_run", "critical_success", "recomputes and writes final CFT JSON (second run)"),
 8: ("compute_run", "critical_success", "reclassifies both rasters with explicit mapping and writes tifs"),
 9: ("data_inspection", "critical_success", "reads CFT.onset source - core formula for onset_hr"),
10: ("compute_run", "critical_success", "computes six JNMF scores and writes required JSON in one step"),
11: ("data_inspection", "neutral", "index/group overview of saliva pickle"),
12: ("data_inspection", "neutral", "reads three csv schemas, model csvs, rule snippets"),
13: ("compute_run", "critical_success", "CFT(60/120/60) run with explicit structure; writes JSON"),
14: ("data_inspection", "critical_success", "full CFT.onset source listing"),
15: ("data_inspection", "neutral", "prints three rule files"),
16: ("data_inspection", "critical_success", "truth uniqueness check and figure-encoding derivation"),
17: ("method_design", "critical_success", "defines Morgan features, split defs, GridSearch plan"),
18: ("method_design", "critical_success", "task_code/figure/response encoders plus MFA stats"),
19: ("data_inspection", "critical_success", "line-numbered sources of six CFT methods"),
20: ("data_inspection", "neutral", "AST walk of rule sources"),
21: ("data_inspection", "neutral", "accuracy summary, model csvs, rule sources"),
22: ("data_inspection", "neutral", "recursive file listing and csv schemas"),
23: ("data_inspection", "critical_success", "finds biopsykit CFT module; HR window statistics"),
24: ("data_inspection", "neutral", "accuracy matrix and full model/rule dumps"),
25: ("data_inspection", "critical_success", "sources of six CFT methods"),
26: ("data_inspection", "neutral", "ccobra syllogistic member inventory"),
27: ("method_design", "critical_success", "Morgan featurization and grid search definition (correct splits)"),
28: ("compute_run", "critical_success", "PSS-10 scoring and output CSV in a single step"),
29: ("data_inspection", "critical_success", "confirms MultiIndex condition/subject/sample structure"),
30: ("compute_run", "critical_success", "computes cortisol features and writes saliva_pred.json"),
31: ("data_inspection", "neutral", "environment and data sanity check"),
32: ("compute_run", "critical_success", "ccobra-encoding evaluation of models vs MFA; writes accuracies.csv"),
33: ("data_inspection", "critical_success", "reads compute_cft_parameter source"),
34: ("data_inspection", "critical_success", "full MFA table per sequence vs existing truth"),
35: ("compute_run", "critical_failure", "fixes wrong response order and sum-combination into final csv"),
36: ("data_inspection", "neutral", "pipeline sources 260 lines"),
37: ("method_design", "critical_failure", "pre-clean + split hrv calls design (anchor mismatch for task 34)"),
38: ("output_write", "critical_failure", "re-runs pipeline and writes wrong sleep endpoints"),
39: ("data_inspection", "neutral", "pipeline signatures, doc, magnitude quantiles"),
40: ("data_inspection", "neutral", "directory listing, package checks"),
41: ("data_inspection", "neutral", "order/similarity exploration to decide implementation"),
42: ("data_inspection", "neutral", "flatten-order hypothesis comparison for W matrices"),
43: ("compute_run", "critical_failure", "sum(axis=1) combination written to final csv"),
44: ("data_inspection", "neutral", "function signatures/docs and index cadence stats"),
45: ("compute_run", "critical_failure", "order x weighting grid experiment picks wrong combo"),
46: ("compute_run", "critical_failure", "StratifiedKFold threshold sweep (gold uses grouped CV)"),
47: ("method_design", "critical_failure", "Otsu threshold + RF design deviates from gold binarization"),
48: ("compute_run", "critical_failure", "runs acceleration pipeline, writes endpoints (boundary error)"),
49: ("compute_run", "critical_failure", "ecg_clean then split hrv calls produce 57/91 features"),
50: ("method_design", "critical_failure", "hand-rolled RSP bandpass/peak pipeline deviates from gold"),
51: ("method_design", "critical_failure", "Otsu + pipeline definition (second run)"),
52: ("data_inspection", "neutral", "walk tree, package specs, pickle overview"),
53: ("method_design", "critical_failure", "hand-rolled RRV pipeline (second run)"),
54: ("data_inspection", "neutral", "walk tree and pickle describe"),
55: ("data_inspection", "neutral", "raw file dumps and Ragni summary (successful run)"),
56: ("data_inspection", "neutral", "focused csv/script inspection (failed run)"),
57: ("data_inspection", "neutral", "alignment and nonfinite checks before modeling"),
58: ("compute_run", "critical_failure", "RandomizedSearchCV run lands F1 0.723 below threshold"),
59: ("compute_run", "critical_success", "full search run lands F1 above threshold (successful run)"),
60: ("data_inspection", "neutral", "file listing, csv schemas, rule excerpts (failed run)"),
}

def main() -> None:
    rows = [json.loads(l) for l in IN.open()]
    with OUT.open("w") as f:
        for r in rows:
            st, role, rat = A[r["sample_idx"]]
            f.write(json.dumps({
                "sample_idx": r["sample_idx"], "task_id": r["task_id"],
                "stratum": r["stratum"], "run_outcome": r["run_outcome"],
                "step_idx": r["step_idx"], "step_type": st,
                "role_in_outcome": role, "rationale": rat,
            }) + "\n")
    from collections import Counter
    tc = Counter(v[0] for v in A.values())
    rc = Counter(v[1] for v in A.values())
    print("step_type:", dict(tc))
    print("role:", dict(rc))
    print("wrote", OUT, len(rows), "rows")

if __name__ == "__main__":
    main()
