# P2a mechanism matrix (edit-step execution error types, in-point runs)

## All in-point runs: edit-step error type x arm

| error_type | ds | mini | qwen | resample |
|---|---|---|---|---|
| assert | 0 | 1 | 0 | 0 |
| data_state | 1 | 1 | 1 | 2 |
| dependency | 1 | 0 | 12 | 3 |
| name_attr | 3 | 3 | 13 | 2 |
| no_code | 19 | 10 | 0 | 0 |
| none | 105 | 109 | 30 | 128 |
| other_error | 4 | 11 | 36 | 2 |

## Signal points only: edit-step error type x arm

| error_type | ds | mini | qwen | resample |
|---|---|---|---|---|
| assert | 0 | 1 | 0 | 0 |
| name_attr | 2 | 2 | 5 | 0 |
| no_code | 6 | 2 | 0 | 0 |
| none | 30 | 30 | 22 | 38 |
| other_error | 0 | 1 | 25 | 0 |

## Signal points: post-edit trajectory health x arm

| arm | n | mean post_exec_fails | edit-step exit!=0 % | retried-modified % | reached_final % |
|---|---|---|---|---|---|
| ds | 38 | 0.16 | 5% | 84% | 95% |
| mini | 36 | 0.06 | 11% | 53% | 97% |
| qwen | 52 | 0.08 | 58% | 90% | 100% |
| resample | 38 | 0.05 | 0% | 66% | 95% |
