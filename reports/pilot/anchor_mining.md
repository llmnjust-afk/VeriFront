# Anchor mining — agent-vs-gold divergences in stable-failure tasks

Method: for each stable-fail task (0/2 at frozen config), extract the agent's final
executed program (`step_NN.py`) and diff its scientific method against the gold
program's. The divergence that plausibly explains the failing columns is the
**recovery anchor**: a minimal, single-clause intervention that should flip Y if
injected as a hint. These become P1's counterfactual intervention targets.

## Task 34 (HRV indices) — 57/91 in ALL THREE runs (exact)

- Gold (3-line essence): `nk.ecg_peaks(raw["ECG"], sampling_rate=100)` on the RAW
  signal, then `nk.hrv(peaks, sampling_rate=100)` once.
- Agent: `nk.ecg_clean(...)` FIRST, then `ecg_peaks(cleaned, correct_artifacts=True)`,
  then three separate calls (`hrv_time` / `hrv_frequency(normalize=True)` /
  `hrv_nonlinear`), plus an injected `RPeaks_N` column and an auxiliary rpeaks file.
- Divergence class: **over-engineering / double preprocessing**. Cleaning before
  peak detection shifts R-peak positions -> every RR-derived metric shifts; agents
  got 432 peaks / mean RR 692 ms vs gold's raw-signal detection. 34/91 columns fail
  (exactly the RR-dependent ones); column set also differs slightly.
- Hypothesized anchor hint (1 clause): "Detect R-peaks on the raw ECG signal as
  provided; do not pre-clean beyond the library's own internal handling."
- Cost if flipped: ~2.4 CA/run; task moves stable-fail -> stable-pass.

## Task 60 (NVC accuracies) — 0/4 runs

- Gold semantics (three quirks): (1) "truth" = most frequent MFA human answer per
  syllogism (`mfa = counts.argmax`), not a logical ground truth; (2) NVC-rule
  fallback: `if prediction_nvc != ['NVC']: prediction_nvc = prediction_model` —
  the rule only counts when it predicts NVC itself; (3) fractional hit
  `int(resp in preds)/len(preds)`, `improvement = hit_nvc - hit_model`.
- Agent: recomputed MFA to CHECK against a supplied truth column (conflated the
  two), implemented rule application directly, hit scoring matches gold's
  fractional rule; fails because the truth/nvc-fallback chain is inverted.
- Divergence class: **task-convention knowledge gap** (benchmark-specific scoring
  convention that cannot be guessed from the data alone).
- Hypothesized anchor hint: state the exact improvement/hit derivation (truth =
  per-syllogism majority MFA response; non-NVC rule predictions are replaced by
  the model prediction before scoring).

## Task 18 (DILI RF) — 0/2, data_correctness=True / func_correctness=False both

- Gold: Morgan FP (radius 2, 2048 bits) [data part OK]; RF grid EXACTLY
  `n_estimators in {200,400,600}, min_samples_leaf=[2], max_depth=[15],
  random_state=2, class_weight='balanced_subsample'`; GridSearchCV scoring
  balanced_accuracy; **cluster-grouped cross-validation** (cluster column;
  np.random.seed(55) state machinery; StratifiedKFold(5, shuffle=True) under
  seed(44)).
- Agent: `StratifiedKFold(shuffle=True, random_state=<own>)` — IGNORES the cluster
  grouping; own grid (`{200,500}` / `{100,250}`, no pinned leaf/depth).
- Divergence class: **evaluation-protocol mismatch** (cluster leakage; unpinned
  hyperparameter grid).
- Hypothesized anchor hint: "Cross-validation splits must respect the provided
  compound clusters (GroupKFold on cluster); use the task's canonical grid."
- Note: agent prints "Best 5-fold CV balanced accuracy" — it optimized a
  self-invented protocol; eval checks gold-protocol metrics.

## Task 44 (biopsykit IMU sleep) — 2/3 both runs (near-miss)

- Gold: `total_sleep_duration = 310` (minutes). Agent: `311`.
- Divergence class: **epoch-to-minute boundary rounding** (off-by-one in the
  sleep-wake epoch aggregation). Two of three JSON keys match exactly.
- Hypothesized anchor hint: "Recheck the epoch->minute conversion at sleep
  boundaries (inclusive/exclusive ends) — the expected total is an integer minute
  count consistent with the epoch count rule."
- Cheapest anchor: one-off-by-one; expected flip cost < 1 CA.

## Flaky tasks (1/2) — failure-side passes also mined

Preliminary reading (to be confirmed during annotation):
- 29 (pass 16/16 vs fail 13/16): identical semantics both runs; 3 columns
  borderline under run-to-run numeric drift.
- 67 (14/14 vs 11/14): pattern-set generation differences.
- 5 / 40 / 85 / 92: mine during annotation; 92's failure pass crashed the official
  eval (wrong output shape), i.e., an output-contract violation, not science error.

## Intervention experiment design (P1 next phase)

For each anchor: re-run 2x at frozen config with the anchor hint appended to the
TaskSpec as `extra_rules` (single sentence, no code). Record: flipped? steps to
flip? token cost? Compare against the no-hint pair. Success criterion per anchor:
2/2 pass after hint (34/60/18/44), plus no-hint control stays failing. Budget:
8 runs x ~2.5 CA ~ 20 CA total worst case.
