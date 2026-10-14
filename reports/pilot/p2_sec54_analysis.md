# P2b sec5.4: statistical hardening + protocol retry


## Part A: signal-point arm coverage after fill-to-8

| point | resample | mini | ds | qwen | cells n>=8 |
|---|---|---|---|---|---|
| t40s2 | 10/12 | 10/12 | 10/13 | 11/21 | 4/4 |
| t40s4 | 6/8 | 4/8 | 5/8 | 6/9 | 4/4 |
| t60s4 | 6/11 | 3/8 | 10/10 | 8/13 | 4/4 |
| t60s6 | 7/10 | 1/10 | 6/10 | 3/12 | 4/4 |
| t85s2 | 6/8 | 8/8 | 1/8 | 4/10 | 4/4 |
| t92s1 | 4/8 | 5/8 | 1/8 | 0/12 | 4/4 |

## Part B: protocol-retry experiment (16 planned re-executions)

- RETRY (re-executed after budget_exhausted): n=8; protocol completed: 8/8; final task success: 4/8 (0.50)
- CTRL (re-executed after completed): n=8; protocol completed: 7/8; final task success: 4/8 (0.50)
- RETRY vs CTRL final success: 0.50 vs 0.50 (Fisher p=1.000)
- reading: gap ~ 0 -> budget exhaustion is a random draw; gap < 0 -> correlates with low-quality output.
