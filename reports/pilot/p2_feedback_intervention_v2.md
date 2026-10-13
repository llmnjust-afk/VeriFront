# P2b sec5.5 v2: validator-triggered retry on t40s4


## Trigger = exit_code (n=19 runs)

| cell | n | SR | retry fired | validator-fail at takeover |
|---|---|---|---|---|
| A | 5 | 2/5 (0.40) | 3/5 | 0/5 |
| B | 4 | 4/4 (1.00) | 0/4 | 0/4 |
| C | 4 | 4/4 (1.00) | 0/4 | 0/4 |
| D | 4 | 4/4 (1.00) | 1/4 | 0/4 |
| Qs | 1 | 1/1 (1.00) | 1/1 | 0/1 |
| Qo | 1 | 1/1 (1.00) | 1/1 | 0/1 |

## Trigger = exit_or_validator (n=21 runs)

| cell | n | SR | retry fired | validator-fail at takeover |
|---|---|---|---|---|
| A | 5 | 3/5 (0.60) | 1/5 | 1/5 |
| B | 5 | 3/5 (0.60) | 0/5 | 0/5 |
| C | 5 | 1/5 (0.20) | 1/5 | 1/5 |
| D | 6 | 4/6 (0.67) | 1/6 | 1/6 |

## v2 vs v1 comparison (same step t40s4)

| cell | v1 trigger rate | v2 trigger rate | v1 SR | v2 SR |
|---|---|---|---|---|
| A | 3/5 | 1/5 | 2/5 | 3/5 |
| B | 0/4 | 0/5 | 4/4 | 3/5 |
| C | 0/4 | 1/5 | 4/4 | 1/5 |
| D | 1/4 | 1/6 | 4/4 | 4/6 |

## mini rescue analysis (v2)

- mini v2 runs: 11; retry fired: 2; of those eventually succeeded: 0
- D vs C (v2): 4/6 vs 1/5, Fisher p=0.242
