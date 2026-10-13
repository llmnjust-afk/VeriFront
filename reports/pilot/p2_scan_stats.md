# P2b full-step scan: inferential statistics

- scanned runs (sandbox-valid): 193

## T1 Per-step per-arm SR [Wilson 95% CI], Fisher p vs same-step resample, BH-FDR q


### t40

| step | resample | mini | ds | qwen |
|---|---|---|---|---|
| 1 | 1/2 (0.50 [0.09,0.91]) | 0/2 (0.00 [0.00,0.66]) p=1.000 | 0/2 (0.00 [0.00,0.66]) p=1.000 | 1/1 (1.00 [0.21,1.00]) p=1.000 |
| 2 | 4/6 (0.67 [0.30,0.90]) | 4/6 (0.67 [0.30,0.90]) p=1.000 | 6/6 (1.00 [0.61,1.00]) p=0.455 | 3/9 (0.33 [0.12,0.65]) p=0.315 |
| 3 | 2/2 (1.00 [0.34,1.00]) | 2/2 (1.00 [0.34,1.00]) p=1.000 | 0/2 (0.00 [0.00,0.66]) p=0.333 | 1/1 (1.00 [0.21,1.00]) p=1.000 |
| 4 | 5/6 (0.83 [0.44,0.97]) | 2/6 (0.33 [0.10,0.70]) p=0.242 | 4/7 (0.57 [0.25,0.84]) p=0.559 | 5/5 (1.00 [0.57,1.00]) p=1.000 |
| 5 | 4/4 (1.00 [0.51,1.00]) | 2/2 (1.00 [0.34,1.00]) p=1.000 | 2/2 (1.00 [0.34,1.00]) p=1.000 | 2/2 (1.00 [0.34,1.00]) p=1.000 |

### t60

| step | resample | mini | ds | qwen |
|---|---|---|---|---|
| 1 | 0/2 (0.00 [0.00,0.66]) | 1/2 (0.50 [0.09,0.91]) p=1.000 | 2/2 (1.00 [0.34,1.00]) p=0.333 | 0/1 (0.00 [0.00,0.79]) p=1.000 |
| 2 | 0/6 (0.00 [0.00,0.39]) | 1/6 (0.17 [0.03,0.56]) p=1.000 | 3/6 (0.50 [0.19,0.81]) p=0.182 | 0/1 (0.00 [0.00,0.79]) p=1.000 |
| 3 | 2/2 (1.00 [0.34,1.00]) | 0/2 (0.00 [0.00,0.66]) p=0.333 | 0/2 (0.00 [0.00,0.66]) p=0.333 | 0/1 (0.00 [0.00,0.79]) p=0.333 |
| 4 | 5/9 (0.56 [0.27,0.81]) | 3/8 (0.38 [0.14,0.69]) p=0.637 | 7/7 (1.00 [0.65,1.00]) p=0.088 | 4/9 (0.44 [0.19,0.73]) p=1.000 |
| 5 | 2/2 (1.00 [0.34,1.00]) | 0/2 (0.00 [0.00,0.66]) p=0.333 | 2/2 (1.00 [0.34,1.00]) p=1.000 | 0/1 (0.00 [0.00,0.79]) p=0.333 |
| 6 | 1/2 (0.50 [0.09,0.91]) | 1/2 (0.50 [0.09,0.91]) p=1.000 | 2/2 (1.00 [0.34,1.00]) p=1.000 | 0/2 (0.00 [0.00,0.66]) p=1.000 |
| 7 | 2/2 (1.00 [0.34,1.00]) | 2/2 (1.00 [0.34,1.00]) p=1.000 | 1/2 (0.50 [0.09,0.91]) p=1.000 | 1/1 (1.00 [0.21,1.00]) p=1.000 |
| 8 | 5/6 (0.83 [0.44,0.97]) | 3/6 (0.50 [0.19,0.81]) p=0.545 | 5/6 (0.83 [0.44,0.97]) p=1.000 | 5/5 (1.00 [0.57,1.00]) p=1.000 |
| 9 | 2/2 (1.00 [0.34,1.00]) | 2/2 (1.00 [0.34,1.00]) p=1.000 | 2/2 (1.00 [0.34,1.00]) p=1.000 | 1/1 (1.00 [0.21,1.00]) p=1.000 |

- 42 step-arm tests; BH-FDR q<0.10: **0**

## T2 Step classification by resample baseline health

| task-step | resample SR | class |
|---|---|---|
| t40s1 | 1/2 (0.50) | capability-dependent (resample healthy) |
| t40s2 | 4/6 (0.67) | capability-dependent (resample healthy) |
| t40s3 | 2/2 (1.00) | capability-dependent (resample healthy) |
| t40s4 | 5/6 (0.83) | capability-dependent (resample healthy) |
| t40s5 | 4/4 (1.00) | capability-dependent (resample healthy) |
| t60s1 | 0/2 (0.00) | task-structural (resample weak) |
| t60s2 | 0/6 (0.00) | task-structural (resample weak) |
| t60s3 | 2/2 (1.00) | capability-dependent (resample healthy) |
| t60s4 | 5/9 (0.56) | capability-dependent (resample healthy) |
| t60s5 | 2/2 (1.00) | capability-dependent (resample healthy) |
| t60s6 | 1/2 (0.50) | capability-dependent (resample healthy) |
| t60s7 | 2/2 (1.00) | capability-dependent (resample healthy) |
| t60s8 | 5/6 (0.83) | capability-dependent (resample healthy) |
| t60s9 | 2/2 (1.00) | capability-dependent (resample healthy) |

### Per-class mean ΔSR (arm minus resample, pooled within class)

| class | arm | pooled ΔSR |
|---|---|---|
| task-structural (resample weak) | mini | +0.25 |
| task-structural (resample weak) | ds | +0.62 |
| task-structural (resample weak) | qwen | +0.00 |
| capability-dependent (resample healthy) | mini | -0.28 |
| capability-dependent (resample healthy) | ds | -0.04 |
| capability-dependent (resample healthy) | qwen | -0.17 |

## T3 P1 signal-step replication inside the scan (same parent)

| point | P1 ΔSR(mini vs res) | scan ΔSR(mini vs res) | sign agree |
|---|---|---|---|
| t40s4 | -0.50 | -0.50 | YES |
| t60s4 | -0.38 | -0.18 | YES |

## T4 Pooled CMH test across capability-dependent steps

| arm | steps pooled | pooled OR | CMH p |
|---|---|---|---|
| mini | 12 | 0.26 | 0.0073 |
| ds | 12 | 0.87 | 0.7615 |
| qwen | 12 | 0.52 | 0.2249 |
