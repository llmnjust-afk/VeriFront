# Step annotation handbook v2 (v1 revised after the 60-step trial round)

Changelog from v1 (motivated by the v1 trial round, kappa 0.357 / role ~0):
1. ROLE labels are now **semi-blind**: every annotator receives, per step, the
   run-level outcome, the step's execution status, and an observation digest.
   (v1 gave the B side code only, which made `critical_success` undecidable and
   collapsed role kappa to ~0. Blindness still applies to the OTHER annotator's
   labels — never to run facts.)
2. Sharper tie-breaker judgments for the three dominant v1 disagreement modes:
   compute_run vs output_write, data_inspection vs eval_check, method_design vs
   compute_run (see C1-C3).
3. New rule for steps that ERRORED and were later repaired (C4; found via the
   step 09 IndentationError of task 37 that v1 A-side mislabeled).
4. `content_summary`/`dependency`/`anchor_flag` remain defined as in v1 but are
   NOT part of the kappa gate; the gate is step_type + role_in_outcome.

## 1. Annotation unit

One **step** = one agent action: an `agent_message` event containing exactly one
`<code>` block or one `<final>` block. The following `tool_call`/`tool_result`
pair is the EXECUTION of that step and is not annotated separately. Repeated
identical re-runs of the same unchanged code count as new steps (the decision to
re-run is itself a scientific act). FORMAT_ERROR turns (unparsable output) are
steps of type `fix_rerun` with content_summary "unparsable output".

## 2. Step-type taxonomy (exactly 8, mutually exclusive; pick FIRST match)

1. `data_inspection` — reading data/files/docs to LEARN facts: shapes, columns,
   heads, value ranges, directory listings, package/module/version discovery,
   source-code reading (inspect), semantic probing of datasets. No persistent
   output written except prints.
2. `data_prep` — deterministic transformation of inputs into intermediates or
   final features: loading into arrays, cleaning, resampling, alignment, feature
   extraction (e.g., Morgan fingerprints), subset assembly.
3. `method_design` — implementing the scientific method: model definitions,
   CV protocol construction, signal-processing pipelines, rule systems,
   parameter grids, statistical procedures.
4. `compute_run` — executing a previously designed full pipeline to produce
   candidate results (fit + predict + write candidate outputs), where the design
   was NOT changed this step.
5. `eval_check` — self-verification of THE AGENT'S OWN code or intermediate
   results: sanity checks, comparing candidate output against expected shapes or
   known facts, re-reading the task to check compliance, consistency metrics.
   Probing DATASET semantics (what does this column mean, where is the truth)
   is NOT eval_check — that is `data_inspection`.
6. `fix_rerun` — CHANGING anything (code, method, parameters, data handling) and
   re-executing in response to a failure observed earlier. A near-identical
   rewrite whose only real change repairs an error (e.g., fixing an indent)
   is `fix_rerun`.
7. `output_write` — writing the FINAL artifacts into `pred_results/` (the exact
   required paths) where the computation producing them was ALREADY executed in
   an earlier step; the step's dominant work is formatting/persisting.
8. `final_report` — the `<final>` summary message to the user.

Judgment rules (v2, replacing v1 tie-breakers):

- **C1 (compute vs write).** If the step both computes and writes
  `pred_results/` artifacts, classify by the DOMINANT work: real computation
  (model fitting, pipeline execution, feature computation, transformations over
  data) -> `compute_run`, even if the step ends with a write; pure persisting of
  results already computed -> `output_write`. "First-time full method execution
  + write" is `compute_run` (v1's "designed earlier" phrasing is retired — it
  required unverifiable history).
- **C2 (check vs inspect).** Verification of the agent's own outputs/code ->
  `eval_check`; learning facts about data, library behavior, or the task ->
  `data_inspection`. Comparing an existing benchmark-provided file's contents
  against dataset-derived facts (e.g., truth mapping) is `data_inspection`.
- **C3 (design vs run).** If a step both defines a method AND executes it in the
  same script, look at what dominates the script: a full CV/search/training
  execution makes it `compute_run`; a definitions-only script (functions
  written, nothing heavy executed) is `method_design`.
- **C4 (errored steps).** If the step ERRORED (execution_status != ok), label
  type by the step's INTENT (what it tried to do). Its role is decided by C4'
  below. A later step that repairs it is `fix_rerun` (if near-identical) and may
  carry the success role.
- **C5 (environment checks).** Package/spec/version probes and cwd listings are
  `data_inspection`, never `data_prep`.
- **C6 (multi-dump steps).** Scripts that print many files/tables/sources at
  once are `data_inspection` even if one section computes a small statistic.

## 3. Role-in-outcome (semi-blind; input = outcome + execution status + digest)

- `role_in_outcome` ∈ {critical_success, critical_failure, neutral}.
- **critical_success**: the step's decision made the run's success possible —
  removing or weakening it would plausibly flip Y (counterfactual criterion,
  confirmed later by intervention runs). Typical holders: the decisive
  method/semantic decision, the final corrected execution that produced the
  deliverable. At most 2 per successful run.
- **critical_failure**: the step's wrong decision directly produced the run's
  failure (its isolated correction would most plausibly flip Y to success).
  At most 2 per failed run.
- **neutral**: routine progress AND steps whose error was fully repaired later
  without changing the run's outcome (C4'): the error triggered repair cost but
  did not decide success/failure. If an errored step's wrong content persisted
  into the final deliverable of a failed run, it is critical_failure.
- Steps that merely re-derive an already-correct result are neutral (no
  double-crediting).
- When in doubt between neutral and critical_*, choose neutral.

## 4. Decision rules (v1 items retained where compatible)

- A run that ends budget_exhausted: the missing `output_write` is implicit; do
  not invent a step for it.
- eval_crash runs: the LAST output_write/compute_run step is critical_failure
  by default (output contract violation), pending counterfactual confirmation.
- Do not double-punish: the errored step AND its repair are not both critical.

## 5. Trial procedure (v2 round)

- v1 baseline (archived at commit 20e09a7): step_type kappa 0.357, role kappa
  ~0.003 — role collapsed because the B sheet was fully blind (no outcome,
  no execution status). Root causes recorded; v1 sheets kept as history.
- v2 round: SAME 60 steps (sample_idx fixed), but the B sheet now includes
  run_outcome, step_execution_status, observation_digest (<=400 chars).
  Both annotators re-label step_type + role_in_outcome under handbook v2.
  Gate: kappa >= 0.7 on step_type and on role (3-way). If role still < 0.7,
  adjudicate disagreements in a reconciliation pass and record remaining
  ambiguities as known limitations.
