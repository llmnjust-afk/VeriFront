# Pre-registration: scale-up to the 60-point target (layers 1-2)

Date frozen: 2026-10-15, before any new parent run. Commit at freeze: 0fba43f+.

## Layer 1 - in-distribution +12 points

- Task selection (mechanical, no cherry-picking): the 6 training tasks with the
  FEWEST points in the frozen 38-point set, ties broken by task id ascending:
  **45, 53, 92 (1 point each), 5, 35, 58 (2 points each)**.
- One NEW frontier parent per selected task (gpt-5.5-2026-04-23, default
  config, temperature 0, max_steps 12); accept if eval_success=1, else retry
  the same task once, then move on; record all attempts.
- Point selection (mechanical): per accepted parent, the two pre-registered
  steps are **step_01 and the LAST code step of the trajectory** (kind=code);
  if the last code step IS step_01, use step_02 instead. Rationale: one
  exploration + one deliverable-ish step per task, mirroring the feature-mix
  balance of the original 38 points.
- Runs: 12 points x 4 arms x 2 reps = 96.

## Layer 2 - Chemistry +2 tasks

- Candidate pool: safe chemistry tasks (no Visualization subtask) not yet
  attempted: {22, 51, 95, 97, 101, 102}. Selection: **ascending task id ->
  22, 51**; if a parent fails twice, substitute the next id in order.
- Point selection: identical to the cross-domain rule (all code steps of the
  accepted parent); 2 tasks x 3 steps expected = 6 points x 4 arms x 2 reps
  = 48.

## Analysis plan (frozen)

- Blind annotation with the same codebook v1.3 pipeline; A/B independent;
  disagreements <=1 level averaged, >1 adjudicated; stratum/role neutral for
  layer-2 points (no matrix entry), layer-1 points inherit the frozen matrix.
- Re-run the three-tier analysis with layer-1 points folded into the LOTO
  training set (38 -> 50); layer-2 points stay held-out. All model settings,
  permutation counts and seeds unchanged from p2c_xdomain2_eval.py.
- Decision rules unchanged: H2 supported iff dRMSE<=0 and dRho>=0.1 under LOTO
  on the enlarged set; out-of-distribution tiers reported descriptively.

## Amendment 1 (2026-10-15, after first parent round)

First round: 45/35/58/51 accepted; 53/92/5/22 failed twice each (eval_crash x2,
func_correctness=False, 0/336 tests) and are moved on from per the frozen rule.
Layer-1 candidate pool is EXTENDED in ascending point-count order to the next
tasks: **44, 34, 40, 85** (<=2 attempts each), target still >=6 additional
accepted parents (12 points). Layer-2 substitutes 22 with **95**. No other rule
changes.
