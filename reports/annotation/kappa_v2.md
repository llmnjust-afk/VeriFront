# Step-annotation reliability report (round 2, handbook v2)

Trial set: 60 steps sampled from the third sandbox batch (32 frozen runs),
strata 34 stable_pass / 20 stable_fail / 6 flaky. Annotator A = model
(anchored in run artifacts), annotator B = human author (semi-blind: run
outcome, step execution status, observation digest; blind to A's labels).

## Round 1 (handbook v1, fully blind B) — archived baseline

- step_type kappa 0.357 (26/60 disagreements)
- role kappa ~0.00 — collapsed by design: B could not see run outcomes, so
  `critical_success` was undecidable. Root cause recorded; sheets archived
  (`annotatorA.jsonl`, `annotatorB.jsonl`).

## Round 2 (handbook v2: semi-blind role input; rules C1-C6)

| metric | kappa | disagreements |
|---|---|---|
| step_type | **0.779** (gate passed) | 7/60 |
| role 3-way | 0.545 (moderate) | 13/60 |
| role critical-vs-neutral | 0.485 | 14/60 |

Type disagreements fell from 26 to 7 and converged on three boundary classes
(compute-vs-write, design-vs-run, transformation-vs-run). Role disagreements
concentrated in the counterfactual granularity: B judged single-step corrections
insufficient to flip failed runs (6 of 13); A credited semantic-decision
inspection steps as critical_success (7 of 13).

## Adjudication

13 role disagreements + 4 type disagreements adjudicated argument-wise
(`annotator_gold.jsonl`, field `adjudication`). One A2 transcription error was
caught and fixed (step 47: label had been transcribed from a different task's
entry). Post-adjudication agreement:

| annotator | vs gold step_type | vs gold role |
|---|---|---|
| A (model) | kappa 0.876 | kappa 0.972 |
| B (human) | kappa 0.906 | kappa 0.568 |

Gold distribution: data_inspection 34, compute_run 22, method_design 2,
data_prep 1, fix_rerun 1; role: neutral 33, critical_success 16,
critical_failure 11.

## Decision for the paper

- Handbook quality evidence: step_type kappa 0.779 >= 0.7 gate passed on
  independent double annotation (round 2).
- Role labels enter the counterfactual experiment design via the adjudicated
  gold set; the B-side dissent on counterfactual granularity (single-step
  repair sufficiency) is recorded verbatim in `annotatorB_v2.jsonl` notes and
  will be reported as a known subjectivity in the Limitations.
- Round-1 fully-blind protocol is retained as a negative control demonstrating
  why role labels require outcome information.
