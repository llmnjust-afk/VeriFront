# P2c Held-Out (Cross-Instance / Cross-Task) Validation Report

**Date**: 2026-10-14 | **Commit**: annotation freeze 308eb41 | **Cost**: 0 CA (reanalysis of existing scan runs)

## 1. What was tested

H2's support (LOTO within the 38 points: dRMSE -0.036, dRho +0.165) is an
in-sample-protocol result. This report tests whether the fitted models
generalise to step instances that were never selected, annotated or examined
as prediction targets, at two levels:

- **H-a (instance-level)**: fit M0/M1 on all 38 points (134 obs), predict
  7 held-out scan code-step instances (28 obs). The held-out instances are
  the complete-4-arm scan cells outside the 38-point set: t40s1, t40s3,
  t60s1, t60s3, t60s5, t60s6, t60s7. (t40s5 and t60s9 are `kind: final`
  steps with no executable script and were excluded so the held-out set
  matches the code-step-only composition of the 38 points.)
- **H-b (task-level)**: additionally remove every t40/t60 point from
  training (32 points, 103 obs) so the held-out instances belong to tasks
  the model has never seen any step of.

Honesty notes fixed before unblinding predictions: (i) the held-out
outcomes exist in the scan reports (Fig 2), so this is a held-out
*reanalysis*, not a prospective test; (ii) annotator A's contamination
boundary is wider here (A produced the R2 scan figures), so merged features
carry a declared annotation-independence caveat; (iii) role for held-out
points is set to `neutral` for all arms (no P1 gold-standard role exists
for them) and stratum follows the frozen task matrix (t40=flaky,
t60=stable_pass).

## 2. Results

| level | model | RMSE | rho | AUROC |
|---|---|---|---|---|
| H-a | M0 (controls) | 0.488 | -0.019 | 0.433 |
| H-a | M1 (V+C) | 0.521 | **-0.199** | 0.417 |
| H-b | M0 | 0.548 | -0.079 | 0.422 |
| H-b | M1 | 0.543 | **-0.271** | 0.358 |

- H-a: dRMSE = +0.033, dRho = -0.180. H-b: dRMSE = -0.005, dRho = -0.193.
- Permutation test (20k): M1 held-out rho = -0.194, p(rho >= 0) = 0.837,
  p(rho <= obs) = 0.164 - the negative point estimate carries no
  statistical signal at n = 28.

**Verdict: the M1-over-M0 gain does NOT generalise beyond the 38 annotated
points.** The gain is not significantly reversed; it is absent.

## 3. Why (three mechanisms, data-supported)

1. **Feature-space coverage drift.** 5 of 7 held-out points are pure
   exploration/inspection steps (F1=0, F2=0); in the training set that
   class is 11/38 points and, crucially, its between-arm variance is small.
   The held-out exploration points have large between-arm variance
   (t40s1: resample 0.5, ds 0, mini 0, qwen 1.0; t60s1: resample 0.0,
   ds 1.0, mini 0.5, qwen 0.0) - a regime the features never had to
   discriminate during training.
2. **Trajectory-variance contamination.** t60s1's resample arm is 0/2:
   when the frontier model itself re-executes step 1, the task still fails
   twice - the Y of early steps is dominated by downstream cliff variance
   (t60 hosts three cliff steps), not by the replaceability of the step.
   Training saw this phenomenon at late-step cliff points; held-out early
   steps show it in a step-position regime the model has not mapped.
3. **Prediction collapse to prior.** On held-out points M1's predictions
   compress into 0.20-0.83 with within-point arm spreads < 0.1
   (p2c_xdomain_predictions_ha.csv): the model falls back to a
   mean-plus-arm-prior predictor outside its training manifold. The one
   held-out point M1 confidently marks "hard" (t60s5, p=0.20-0.25) is
   indeed the held-out point with the largest arm disagreement - the
   feature signal exists but is too weak to survive distribution shift.

## 4. Consequences for the paper

1. R4 gains a held-out paragraph reporting the null result verbatim.
2. Abstract and Discussion wording narrows: the verifiability signal is
   established *within the annotated point distribution under the same
   sampling protocol*, not as a general predictor of replaceability.
3. Limitations adds: external validity of the feature-based predictor is
   unverified; held-out validation on 7 instances (28 obs) shows the
   LOTO gain does not transfer.
4. The null result is itself informative for the process-supervision
   literature: cheap blind-coded step features, like learned process
   verifiers, do not automatically transfer out of their sampling regime.

## 5. Files

- scripts/p2c_xdomain_eval.py (lab) / p2c_xdomain_eval.py (local run copy)
- reports/annotation/blind_materials_xdomain.md (leak-checked materials)
- reports/annotation_xdomain/{annotatorA,annotatorB,p2_annotation_merged}_xdomain.csv
- reports/pilot/p2c_xdomain_results.json, p2c_xdomain_predictions_{ha,hb}.csv
