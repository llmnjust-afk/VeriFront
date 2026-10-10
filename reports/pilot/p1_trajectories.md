# P1 trajectory inventory — ScienceAgentBench frontier runs

Frozen config: gpt-5.5-2026-04-23, temperature 0, max_tokens 8192, use_knowledge=true,
12-step CodeAct-lite budget. All tasks objective-eval (judge tasks excluded).
Raw CSV: `reports/pilot/results_p1.csv` (latest stamp per (task, arm) shown here).

## Headline

- Per-run success rate: **18/32 = 0.5625** across 16 objective tasks x 2 runs.
- Six tasks stable-success (2/2): 45, 87, 35, 37, 53, 58.
- Four tasks stable-failure (0/2): 34 (57/91 exactly, all 3 runs incl. 6-step),
  60 (0/4 incl. 6-step), 18 (data_correctness=True, func_correctness=False in both),
  44 (2/3 in both runs — near-miss).
- Six flaky (1/2): 29, 5, 40, 67, 85, 92.
- Cross-run variance is real under temperature 0: 29 flipped (16/16 vs 13/16),
  67 flipped (14/14 vs 11/14), 85 flipped, 92 flipped via eval_crash. Justifies
  >=2 runs per task; also validates the deterministic-anchor choice of task 34.
- Cost (ChatAnywhere default-group ladder, 0.035/0.21 CA per 1K, CA~RMB; USD at 7.15):
  frozen-config 32 runs = 83.2 CA (~11.6 USD); all-time incl. 6-step sweep and the
  discarded judge-eval run = 98.1 CA (~13.7 USD). Well inside budget.
- Heavy tasks: 40 (~8.1 CA each, 180K+ prompt tokens — big CSV context), 44 (~3.6).
- eval_crash semantics: a "completed" run whose output crashes the OFFICIAL eval
  script is scored Y=0 (92 pass2, 60 sensitivity run).

## Per-task frozen-config matrix

| task | run1 | run2 | verdict | notes |
|---|---|---|---|---|
| 5  | 1 | 0 | flaky | func_correctness False on fail |
| 18 | 0 | 0 | stable-fail | data ok, function wrong (both) |
| 29 | 1 | 0 | flaky | 16/16 vs 13/16 (baseline-relative semantics) |
| 34 | 0 | 0 | stable-fail | 57/91 EXACT across 3 runs — prime anchor |
| 35 | 1 | 1 | stable-pass | 12/20 both |
| 37 | 1 | 1 | stable-pass | 3/3 both |
| 40 | 1 | 0 | flaky | F1 0.747 pass vs 0.716 fail; heaviest cost |
| 44 | 0 | 0 | stable-fail | 2/3 both — near-miss |
| 45 | 1 | 1 | stable-pass | 12/12 both |
| 53 | 1 | 1 | stable-pass | land cover 0.96-0.98; protected 1.0 |
| 58 | 1 | 1 | stable-pass | individuals.csv both |
| 60 | 0 | 0 | stable-fail | 0/4 overall; derivation gap (improvement/hit cols) |
| 67 | 0 | 1 | flaky | 11/14 vs 14/14 |
| 85 | 0 | 1 | flaky | N/A verdict (json check) |
| 87 | 1 | 1 | stable-pass | N/A verdict (json check) |
| 92 | 1 | 0 | flaky | pass2 crashed the eval script |

## Anchor candidates for P1 recovery experiments

- Task 34 (stable-fail, exact-score): RR-interval extraction method differs from gold
  (MaxNN off by 560 ms) — one targeted hint should flip 57/91 to pass.
- Task 60 (stable-fail): improvement/hit column derivation mismatch.
- Task 18 (stable-fail): data pipeline right, RF function spec wrong.
- Task 44 (stable-fail, near-miss): 2/3 — single-column gap.
- Flaky six: natural recovery-margin material without any intervention.
