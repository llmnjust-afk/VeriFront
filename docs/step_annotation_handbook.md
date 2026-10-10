# Step annotation handbook v1 (试标注用)

Scope: annotation of agent trajectories on ScienceAgentBench (objective-eval
tasks, frozen config). Purpose: (a) classify every scientific step; (b) mark the
steps whose content materially determined the outcome (anchors). This handbook
fixes the unit, the taxonomy, and the decision rules so two annotators reach
kappa >= 0.7 on a 60-step trial set.

## 1. Annotation unit

One **step** = one agent action: an `agent_message` event containing exactly one
`<code>` block or one `<final>` block. The following `tool_call`/`tool_result`
pair is the EXECUTION of that step and is not annotated separately. Repeated
identical re-runs of the same unchanged code count as new steps (the decision to
re-run is itself a scientific act). FORMAT_ERROR turns (unparsable output) are
steps of type `fix_rerun` with content_summary "unparsable output".

## 2. Step-type taxonomy (exactly 8, mutually exclusive; pick FIRST match)

1. `data_inspection` — reading data/files to LEARN facts: shapes, columns, heads,
   value ranges, directory listings, library-version checks. No persistent output
   written except prints.
2. `data_prep` — deterministic transformation of inputs into intermediates or
   final features: loading into arrays, cleaning, resampling, alignment, feature
   extraction (e.g., Morgan fingerprints), subset assembly.
3. `method_design` — implementing the scientific method: model definitions,
   CV protocol construction, signal-processing pipelines, rule systems,
   parameter grids, statistical procedures.
4. `compute_run` — executing a previously designed full pipeline to produce
   candidate results (fit + predict + write candidate outputs), where the design
   was NOT changed this step.
5. `eval_check` — self-verification WITHOUT changing the method: sanity checks,
   re-reading the task, comparing candidate output against expected shapes or
   known facts, computing consistency metrics.
6. `fix_rerun` — CHANGING anything (code, method, parameters, data handling) and
   re-executing in response to a failure observed earlier.
7. `output_write` — writing the FINAL artifacts into `pred_results/` (the exact
   required paths). A step that both computes and writes finals counts as
   `output_write` only if the computation itself was already designed in an
   earlier step; otherwise it is `compute_run`.
8. `final_report` — the `<final>` summary message to the user.

Tie-breakers: (a) if a step both inspects and transforms, the dominant purpose
wins (>50% of lines); (b) if a step both designs and runs for the first time, it
is `method_design`; subsequent unchanged re-executions are `compute_run`; (c)
anything written to pred_results/ is never `data_inspection`.

## 3. Role-in-outcome fields (annotate for every step)

- `role_in_outcome` ∈ {critical_success, critical_failure, neutral}:
  - `critical_failure`: the step's content, if corrected in isolation, could
    plausibly flip Y (counterfactual criterion; tentative — confirmed only by
    intervention runs). At most the 2 most determinative steps per failed run.
  - `critical_success`: the step established the key correct result (e.g., the
    winning method choice or correct derivation).
  - `neutral`: everything else.
- `content_summary`: one clause, <= 20 words, stating WHAT was done scientifically
  (not code mechanics). Example: "Clean ECG then detect R-peaks on cleaned signal".
- `dependency` (optional, <= 15 words): what this step relied on — a prior step,
  a dataset fact, a library default, or task text.
- `anchor_flag` (bool): true if this step embodies an agent-vs-gold METHOD
  divergence (see reports/pilot/anchor_mining.md). Only for critical_* steps.

## 4. Decision rules

- A step that only FIXES A TYPO/IMPORT is `fix_rerun` but never critical_failure
  unless the typo alone explains the eval failure.
- Steps that re-derive the SAME correct result after a failure are still
  `fix_rerun`; do not double-punish.
- A run that ends budget_exhausted: the missing `output_write` is implicit; do
  not invent a step for it.
- eval_crash runs: the LAST output_write/compute_run step is critical_failure
  by default (output contract violation), pending counterfactual confirmation.
- When in doubt between neutral and critical_*, choose neutral and flag the
  step for discussion in the reconciliation pass.

## 5. Trial set and kappa procedure

- `scripts/make_annotation_sample.py` samples 60 steps stratified over the 16
  frozen-config tasks x 2 runs: >=2 critical candidates from every stable-fail
  run, >=1 critical_success from every stable-pass run, plus the differing step
  pairs from flaky runs.
- Both annotators label step_type + role_in_outcome independently; compute
  Cohen's kappa jointly over the two fields (weight steps where either annotator
  is unsure 'discuss'). Target kappa >= 0.7; revise taxonomy wording before
  scaling if below.
- Output sheet: `reports/annotation/annotation_sample.jsonl` (blank judgment
  fields for the human annotator; machine pre-labels provided for comparison).
