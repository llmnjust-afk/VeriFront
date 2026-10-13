# P2b sec5.3: Qwen 14B-AWQ vs 8B signal-point replication

| point | 8B SR (n) | 14B SR (n) | 14B verdict |
|---|---|---|---|
| t60s6 | 2/10 (0.20) | 1/4 (0.25) | failure persists |
| t85s2 | 4/8 (0.50) | 0/2 (0.00) | new failure at 14B |
| t40s4 | 5/5 (1.00) | 1/4 (0.25) | new failure at 14B |
| t92s1 | 0/8 (0.00) | 0/4 (0.00) | failure persists |
| t60s4 | 4/12 (0.33) | 4/4 (1.00) | repaired at 14B |
| t40s2 | 7/17 (0.41) | 4/4 (1.00) | repaired at 14B |

- pooled signal points: 8B 22/60 (0.37) vs 14B 10/22 (0.45)
- Fisher 14B vs 8B pooled: p=0.610
