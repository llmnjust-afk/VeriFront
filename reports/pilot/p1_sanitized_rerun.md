# P1 sanitized re-run + anchor intervention results

## Contamination event and fix

Trial annotation exposed that the original workdir symlink exposed the FULL
benchmark tree to agents, including `gold_programs/`, `eval_programs/`,
`scoring_rubrics/` (official SAB gives agents only `benchmark/datasets`).
Grep of the 32 frozen-config traces: 17/32 runs mentioned protected paths;
9 runs contained the protected-file canary line in observations (i.e., agents
READ protected content — including all "stable-pass" tasks 45/87/58/67/5/37).
All pre-fix runs were quarantined to `runs_quarantined/` and are exploratory
only; they must not be cited as capability measurements.

Fix (commit 27280d9): `prepare_workdir` now builds `benchmark/` as a real dir
whose only entry is a `datasets` symlink; `run_eval` swaps in the full tree at
eval time. Guard test asserts the agent view contains only `datasets`.

## Clean frozen matrix (16 tasks x 2, gpt-5.5-2026-04-23, temp 0, 12 steps)

Per-run success: **18/32 = 0.5625** (coincidentally equal to the contaminated
batch, but composition changed materially).

- Stable-pass 2/2 (8): 18, 37, 40, 45, 53, 58, 67, 85
- Stable-fail 0/2 (6): 34, 35, 44, 60, 87, 92
- Flaky 1/2 (2): 5, 29

Composition shifts vs contaminated batch: 87 pass->fail (its old passes were
gold-peek artifacts: "verified to exactly match the accessible benchmark gold"),
18 fail->pass, 35 pass->fail (new failure mode: 86k-token exploration loops ->
output shape broke the eval script -> eval_crash), 67 flaky->stable-pass.

Cost: sanitized re-run batch = 112.5 CA (~15.7 USD) incl. hint runs. All-time
spend ~210.6 CA (~29.5 USD).

## Anchor intervention runs (frontier_hint arm, 2 runs each)

One-clause hint appended to TaskSpec as extra_rules:

| task | anchor hypothesis | frozen | hint | verdict |
|---|---|---|---|---|
| 34 | do NOT pre-clean ECG before peak detection; single nk.hrv call | 0/2 | **2/2 (86/91)** | FLIPPED — minimal method hint turns stable-fail into stable-pass |
| 60 | truth = per-syllogism majority MFA response; non-NVC rule predictions replaced by model prediction; fractional hit | 0/2 | 1/2 | PARTIAL flip (one run still budget_exhausted at 93k prompt tokens) |
| 18 | cluster-grouped CV required | 2/2 | 1/2 | ANCHOR REJECTED — clean runs pass without the hint; the old failures were contamination-era artifacts; the eval tolerates non-grouped CV |
| 44 | off-by-one epoch boundary counting | 0/2 | 0/2 | NOT FLIPPED — hint too vague or hypothesis wrong (1/3 and 2/3); needs round-2 mining |

Honest summary: method-level hints flip failures of the "over-engineering"
class (34) and partially the "task-convention knowledge" class (60); they do
NOT fix boundary-semantics failures (44) and can be unnecessary when the
original failure diagnosis was confounded (18).

## Failure-mode notes for round-2 mining

- 34 frozen runs now fail via eval_crash (both) — agent output breaks the eval
  script rather than scoring 57/91; with hint, 86/91 (5 residual columns, likely
  the extra RPeaks_N column / normalize flag). Next: mine the 5 residual columns.
- 44: 1/3 and 2/3 under hint — total_sleep_duration still off; compare agent
  epoch-count expression vs gold's exact pipeline (biopsykit predict_pipeline).
- 92: both runs eval_crash — output contract violation; mine the expected file
  format (N/A verdict json check).
- 87: clean fails with N/A verdict — the polynomial fit output no longer
  matches; coefficients come from a different series/grid point than gold.
- 35: 11/20 in one run; functional-part errors.

## Next steps

1. Regenerate the trial annotation set from the SANITIZED corpus (updated
   strata) for the user's B-side annotation; kappa vs existing A-side practice.
2. Round-2 anchor mining for 44/87/92/35 + hint refinement for 60 (shorter
   hint, maybe +1 step budget to avoid budget_exhausted).
3. Scale decision: SR 0.56 on 16 objective tasks gives adequate contrast for
   the step-annotation phase (>= 60 steps) and the counterfactual analysis.
