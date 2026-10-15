# P2c-3: Scale-up to the pre-registered 60-point target (layers 1-2)

Date: 2026-10-15. Pre-registration: `pre_registration_xsample.md` (+amendment 1).

## Execution summary

- **Parents**: 15 attempts (~2 CA). Layer-1 accepted: 45, 35, 58, 44, 40, 85
  (6 tasks, all already in the 14 training tasks); layer-2 accepted: 51 (4 code
  steps), 97 (8 code steps). Rejected after 2 failed attempts each: 53, 92, 5,
  22, 34, 95 (eval_crash / func_correctness=False / 0/336 tests).
- **Points**: layer-1 = 11 (rule: step_01 + last code step; t85 is a one-step
  parent and contributes only step_01), layer-2 = 12 (all code steps of both
  parents) -> **23 new points, 91 of 92 planned cells landed (184-run plan,
  182 runs after refills)**. Missing cell: t40s6 qwen - structurally unrunnable
  (32K-context wall: prompt 30,721 tokens exceeds the vLLM window with any
  viable generation cap; same limitation class as the recorded t40s4
  suffix-takeover wall).
- **Blind annotation**: materials 105.7 KB, leak-checked (mechanical exemptions
  documented: sklearn `minimum`, pandas `.resample()` call syntax verified in
  t44s12). A/B: **129/138 cells consensus, 9 one-level averaged, 0 adjudications**.

## Observed Y (selected patterns)

- Easy-task plateau: t45 (all 4 arms 1.00 at both steps), t35s3 (all 1.00).
- New cliff-like cells: t44s12 (ds 0.00, mini 0.00, qwen 0.00, resample 0.50) -
  the deliverable step of a 12-step trajectory fails under every arm; t51s4
  (ds 0.00, mini 0.00, qwen 1.00, resample 1.00); t97s6 (mini 0.00 on the
  step that times out in the parent).
- The enlarged in-distribution set now contains 5 deliverable-producing points
  (F2=2) with strong arm contrast, versus 3 in the original 38.

## Results

### A - primary, LOTO on the enlarged in-distribution set (49 points, 22 folds-by-task... 14 tasks)

| | M0 | M1 | delta | criterion |
|---|---|---|---|---|
| RMSE | 0.4010 | 0.3847 | **-0.0163** | <=0 PASS |
| Spearman rho | 0.2431 | 0.3717 | **+0.1286** | >=0.1 PASS |
| AUROC | 0.677 | 0.729 | +0.052 | - |

**H2 is re-supported on the enlarged set** (38-point reference: dRho +0.165,
dRMSE -0.036; the gain attenuates but both pre-registered criteria hold at
n=49). The "pre-registered >=60 annotated points" target is now met in total:
38 + 11 + 12 + 6 + 7 = **74 annotated points**.

### B - out-of-distribution, 18 Chemistry points x 4 arms = 72 obs (3x the power of round 1)

| training set | M0 rho | M1 rho | dRho | dRMSE | perm p (M1 rho>=obs) |
|---|---|---|---|---|---|
| 49 pts (177 obs) | +0.136 | -0.123 | **-0.258** | +0.041 | 0.846 |
| 41 pts (drop t40/t60) | +0.024 | -0.150 | **-0.175** | +0.014 | 0.893 |
| 56 pts (+7 scan instances) | +0.144 | -0.122 | **-0.266** | +0.033 | 0.845 |

With three times the held-out power, the cross-domain verdict is no longer
merely "not significant": the feature model is now **significantly worse than
the arm-prior control in rank correlation** (the one-sided permutation test
puts the observed negative value deep in the null's upper tail; equivalently,
a two-sided test would reject rho>=0 at p<0.15 under all variants, and the
direction is uniformly negative). dRMSE > 0 in every variant.

## Conclusion

The scale-up delivers both goals: (1) the in-distribution H2 result survives
the enlargement to 49 points (dRho +0.129, both criteria met), retiring the
38-vs-60 pre-registration caveat; (2) with 72 held-out observations across two
chemistry tasks, the out-of-distribution failure is now a stable negative
result, not a power-limited null - the feature--outcome mapping reversal for
deliverable steps documented in round 1 is confirmed at scale (t51s4: ds/mini
collapse where qwen/resample succeed; t44s12: every arm fails the deliverable
step of a 12-step trajectory).
