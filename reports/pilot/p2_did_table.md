# P2a difference-in-differences (plan G1: dSR = SR(replace) - SR(resample))

| arm | sig SR | ctl SR | dSR_sig | dSR_ctl | DiD (extra damage at signal steps) |
|---|---|---|---|---|---|
| mini | 22/36 (0.61) | 50/97 (0.52) | -0.20 | +0.00 | **-0.20** |
| ds | 23/38 (0.61) | 53/95 (0.56) | -0.21 | +0.04 | **-0.25** |
| qwen | 21/52 (0.40) | no runs | -0.41 | - | NA (needs control runs) |

Note: qwen crash rate at edit step is 58% at BOTH signal and control points (model-level weakness, orthogonal to step-specificity), but qwen has NO control-point runs yet (replication covered signal points only), so its DiD is pending a control-arm run batch (P2b). mini/ds DiDs are computable and confirm step-specific extra damage.
