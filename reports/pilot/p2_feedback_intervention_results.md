# P2b sec5.5 feedback-intervention pilot: results

- total intervention runs: 51 (2 qwen dry-runs reported separately)

## Per-cell summary (pooled over 3 steps)

| cell | arm x feedback | n | SR | retry-triggered | SR|triggered |
|---|---|---|---|---|---|
| A | resample x bare-retry | 13 | 7/13 (0.54) | 3/13 | 1/3 |
| B | resample x structured | 12 | 9/12 (0.75) | 1/12 | 1/1 |
| C | mini x bare-retry | 12 | 4/12 (0.33) | 0/12 | - |
| D | mini x structured | 12 | 5/12 (0.42) | 1/12 | 1/1 |
| Q-struct | qwen x structured (dry) | 1 | 1/1 (1.00) | 1/1 | 1/1 |
| Q-orig | qwen x bare-retry (dry) | 1 | 1/1 (1.00) | 1/1 | 1/1 |

## Per-step detail

| cell | t40s4 | t60s4 | t60s2 |
|---|---|---|---|
| A | 2/5 | 3/4 | 2/4 |
| B | 4/4 | 2/4 | 3/4 |
| C | 4/4 | 0/4 | 0/4 |
| D | 4/4 | 0/4 | 1/4 |
| Q-struct | 1/1 | - | - |
| Q-orig | 1/1 | - | - |

## Main test: feedback effect by arm (pooled)

- mini: structured vs bare-retry (D vs C): ΔSR = +0.08 (Fisher p=1.000)
- resample: structured vs bare-retry (B vs A): ΔSR = +0.21 (Fisher p=0.411)

- **Interaction (D-C) - (B-A) = -0.13**
  - > 0 supports 'feedback-missing' component (structured feedback helps weak models more);
  - ~ 0 / < 0 supports 'capability-missing' component.

## Retry-window mechanics

- A: retry triggered 3/13; post-retry step rescued to eventual success in 1/3 triggered runs
- B: retry triggered 1/12; post-retry step rescued to eventual success in 1/1 triggered runs
- C: retry triggered 0/12; post-retry step rescued to eventual success in 0/0 triggered runs
- D: retry triggered 1/12; post-retry step rescued to eventual success in 1/1 triggered runs
