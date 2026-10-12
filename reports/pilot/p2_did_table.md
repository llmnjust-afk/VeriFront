# P2a difference-in-differences (plan G1: dSR = SR(replace) - SR(resample))

| arm | sig SR | ctl SR | dSR_sig | dSR_ctl | DiD (extra damage at signal steps) |
|---|---|---|---|---|---|
| mini | 22/36 (0.61) | 52/100 (0.52) | -0.20 | +0.00 | **-0.21** |
| ds | 23/38 (0.61) | 53/95 (0.56) | -0.21 | +0.04 | **-0.25** |
| qwen | 21/52 (0.40) | 34/42 (0.81) | -0.41 | +0.29 | **-0.71** |

## Common-control-set DiD (10 shared control points, sandbox-invalid excluded)

| arm | sig SR | ctl10 SR | dSR_sig | dSR_ctl10 | DiD_common |
|---|---|---|---|---|---|
| mini | 22/36 (0.61) | 43/65 (0.66) | -0.20 | +0.03 | **-0.24** |
| ds | 23/38 (0.61) | 42/61 (0.69) | -0.21 | +0.06 | **-0.27** |
| qwen | 21/52 (0.40) | 34/40 (0.85) | -0.41 | +0.22 | **-0.63** |

Notes: (i) qwen edit-step crash rate is 58% at both signal and control points (model-level weakness, orthogonal to step-specificity); (ii) qwen control advantage over resample at ctl10 is driven partly by repair wins at t35s1 (3/4 vs 1/4) and small-sample points (t18s2/s3, t60s8); (iii) pooled and common-set DiDs agree in ordering: qwen > ds > mini in step-specific extra damage.
