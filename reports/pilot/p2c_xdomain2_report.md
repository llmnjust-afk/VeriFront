# P2c-2: TRUE cross-domain evaluation (Computational Chemistry, tasks 1 & 3)

Date: 2026-10-15. Pre-registered point rule: **all 3 code steps of each parent**
(final steps excluded) -> 6 points x 4 arms x 2 reps = 48 planned runs.

## Design

Training tasks cover Bioinformatics (4), GIS (1), Psychology (8); **zero**
Computational Chemistry tasks (SAB verified set: 20 chemistry tasks). Tasks 1
(ClinTox toxicity/FDA multitask prediction) and 3 (bulk-modulus regression via
physics-relation residual decomposition) are therefore unseen-domain targets.

Parents (frontier gpt-5.5-2026-04-23, eval_success=1):
- sab_1 @1792027104-2691932 (57 s), sab_3 @1792027829-2732525 (68 s).
- Discarded parents: sab_26 (eval_crash), sab_16 x2 (overlap 0.914/0.912),
  sab_2 (eval_detail N/A) - 6 CA spent on parent attempts.

Runs: 46/48 landed (two ds cells at 1 rep after repeated relay read-timeouts;
every (point, arm) cell has >=1 obs). eval_crash is coded Y=0 exactly as in the
original 767-run inventory (73 such runs there, 9.5%).

## Blind annotation

Materials regenerated for the 6 chemistry points (38,796 chars, leak-checked;
the only "mini" hits were `minimum` in sklearn calls, excluded mechanically).
A and B coded independently: **34/36 cells consensus, 2 one-level disagreements
averaged, 0 adjudications**. Frozen features:

| point | F1 | F2 | F3 | F4 | F5 | F6 | note |
|-------|----|----|----|----|----|----|------|
| t1s1  | 0 | 0 | 1 | 1 | 0   | 1 | env/data exploration |
| t1s2  | 0 | 0 | 1 | 1 | 0.5 | 1 | data overview (B: F5=1) |
| t1s3  | 1 | 2 | 2 | 1 | 1   | 1 | full modelling -> pred_results |
| t3s1  | 0 | 0 | 1 | 1 | 0   | 1 | file-tree/schema inspection |
| t3s2  | 1 | 1 | 1.5 | 2 | 0 | 1 | diagnostics; parent exited 1 (B: F3=1) |
| t3s3  | 1 | 2 | 2 | 1 | 1   | 1 | final modelling, reuses step-2 physics stat |

Stratum/role: tasks 1/3 absent from the frozen stability matrix and without P1
gold labels -> neutral stratum (baseline) and neutral role, the same
conservative choice as the held-out reanalysis.

## Observed Y (cell means)

- t3 (all steps, all arms): Y = 1.00. Notably t3s2 **failed in the parent
  trajectory** (exit 1) yet every resample/replacement arm succeeded - the
  parent's failure was not systematic.
- t1s3: ds 1.00, mini 0.00, qwen 0.00, resample 0.00 (2/2 each) - the only
  strongly arm-separated cell; self-contained fingerprint+RF pipeline survived
  only under ds edits.
- t1s1/t1s2: within-point spread 0-1 across arms.

## Results (6 held chemistry points, 24 obs; 20k permutations)

| training set | M0 rho | M1 rho | dRho | M0 RMSE | M1 RMSE | M0 AUC | M1 AUC | perm p (M1 rho>=obs) |
|---|---|---|---|---|---|---|---|---|
| Ha: 38 pts (134 obs) | +0.146 | +0.122 | **-0.023** | 0.407 | 0.441 | 0.637 | 0.705 | 0.288 |
| Hb: 30 pts (drop t40/t60, 103 obs) | -0.061 | +0.127 | **+0.187** | 0.413 | 0.424 | 0.426 | 0.716 | 0.278 |
| Hc: 45 pts (Ha + 7 held scan instances, 162 obs) | +0.013 | +0.060 | **+0.047** | 0.428 | 0.438 | 0.553 | 0.695 | 0.394 |

**No variant shows a significant M1 gain; RMSE is never improved.** The
in-protocol LOTO gain (dRho = +0.165) does not survive a domain shift.

## Mechanism (prediction-level)

M1 collapses deliverable steps (t1s3, t3s3: F1=1,F2=2,F3=2,F5=1) to
p = 0.26-0.31, importing the training domain's "late complex steps often
fail" prior. In chemistry, t3s3 succeeded under **all four arms** (a compact
physics-relation residual decomposition) - the feature-outcome mapping
**reverses** for this stratum. Exploration steps get p = 0.68-0.83 and are
roughly right for t3 but wrong for the volatile t1s1/t1s2. M0 predicts a flat
0.63-0.69 everywhere (arm prior + intercept); its small positive rho is an
artifact of ds's elevated mean (0.833) ranking first on two cells.

## Conclusion

Third rung of the generalisation ladder: within-annotation-set LOTO
supported H2 (dRho +0.165); same-task new instances reversed it (dRho
-0.18 to -0.27); a fully unseen domain gives dRho between -0.02 and +0.19
with permutation p >= 0.28 in every training variant. The feature-guided
allocation gain is an **in-distribution effect**: it does not transfer to
unseen tasks or domains. Consistent with the held-out analysis, the failure
is mechanistic (feature-space coverage drift + reversed outcome mapping for
deliverable steps), not noise: with 24 obs the point estimates are stable
across all three training variants.
