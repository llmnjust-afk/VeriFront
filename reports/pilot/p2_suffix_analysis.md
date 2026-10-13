# P2b sec5.2: suffix-takeover vs single-step replacement

- runs analyzed (t40s4/t60s4, sandbox-valid, non-intervention): 73

| point | arm | mode | n | SR |
|---|---|---|---|---|
| t40s4 | resample | single | 6 | 5/6 (0.83) |
| t40s4 | mini | single | 6 | 2/6 (0.33) |
| t40s4 | mini | suffix | 7 | 1/7 (0.14) |
| t40s4 | qwen | single | 5 | 5/5 (1.00) |
| t60s4 | resample | single | 9 | 5/9 (0.56) |
| t60s4 | mini | single | 8 | 3/8 (0.38) |
| t60s4 | mini | suffix | 6 | 0/6 (0.00) |
| t60s4 | qwen | single | 9 | 4/9 (0.44) |
| t60s4 | qwen | suffix | 3 | 0/3 (0.00) |

## Suffix amplification (SR_suffix - SR_single)

- t40s4 mini: 0.14 vs 0.33 -> -0.19
- t60s4 mini: 0.00 vs 0.38 -> -0.38
- t60s4 qwen: 0.00 vs 0.44 -> -0.44

## Context wall (32K-class models cannot takeover t40s4 suffix)

- t40s4 prompt ~28.7K tokens; suffix generation adds multi-turn growth ->
- qwen-suffix t40s4: 3/3 runs HTTP 400 (context exceeded) -- recorded as infeasible, not as failure;
- mini-suffix t40s4: completed 6/6 (mini endpoint accepts the length; quality outcome below).
