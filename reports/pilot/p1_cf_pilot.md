# P1-CF 试点小结（CF0 + CF1）— 2026-10-10

设计依据：`docs/design_counterfactual.md`（方案 A 确定性重放 + 步级接管）。实现：`verifront/cf/replay.py`、`CodeActAgent.run_from`、`scripts/run_cf_point.py`（commit 5b67d28, 3d3c21a）。

## CF0 — task 45 step_01（空前缀，管线冒烟 + 点级对照）

| 臂 | n | 结果 |
|---|---|---|
| cf_frontier_resample | 3 | 3/3 Y=1 (12/12) |
| cf_local_replace (gpt-5.4-mini) | 2 | 2/2 Y=1 (12/12) |
| cf_local_replace (deepseek-v3.2) | 2 | 2/2 Y=1 (12/12) |

- 点级 ΔSR = 0：45 的 s01（PSS 问卷计分，gold: compute_run/critical_success）**小模型即可完成**——critical_success ≠ 前沿必需的第一个数据点（H1a）。
- 附：首批 6 条 run 因 `--edit-model` 键名笔误（model vs model_id）在写 result 前全灭（~5 CA 损失）；教训 = 批前必单条干跑。

## CF1 — 前缀重放保真验证

**37 s05**（parent 1791612745-277512，重放 4 步）：

| 臂 | n | 结果 |
|---|---|---|
| resample | 1 | 1/1 Y=1 (3/3) |
| mini replace | 2 | 2/2 Y=1 (3/3) |
| deepseek replace | 2 | 2/2 Y=1 (3/3) |

保真：4 步重放全部 ok→ok；观察 diff 仅 6–7 字符，逐字核对全部为 **matplotlib 随机临时缓存路径**（/var/tmp/matplotlib-<rand>）——非语义差异。文件 manifest 与 parent 一致（step 文件之外无产物差异；run 目录本就不拷回产物）。

**60 s08**（parent 1791614180-321913，重放 7 步）：

| 臂 | n | 结果 |
|---|---|---|
| resample | 2 | 2/2 Y=1 |
| mini replace | 2 | 2/2 Y=1 |
| deepseek replace | 2 | **1/2**（pass1 失败，pass2 通过） |

失败 run（cf1791647945-382855）失效机理：deepseek 接管步**直接输出 FINAL_ANSWER**（premature final，trace extra.parsed_action=final），跳过剩余 4 步 → 无产物 → eval_crash（无 verdict）。**协议失效而非能力失效**——已在 cf_meta 增记 `edit_step_parsed_action` 以便后续分层统计（capability vs protocol failure）。

## 结论与 gate 判定

- 方案 A 重放可行：消息层逐字节重建 ✓，文件系统层重执行保真 ✓（差异仅环境噪声），后续 frontier 步在重放状态上正常工作（所有 resample/替换臂延续至完成）。
- 点级信号：45 s01 ΔSR=0；37 s05 ΔSR=0；60 s08 ΔSR(deepseek)=0.5（n=2，协议失效主导）——flaky 点需 n≥3 复核。
- 成本：CF0+CF1 共 14 条 run ≈ **8.8 CA**（frontier 臂 7.7，mini 0.9，deepseek 下界 0.2）。外推：全量扩展（~200 run）≈ 120–180 CA，预算可行。
- **Gate 通过 → 进入全量替换点扩展**（gold: 16 cs + 11 cf + 每任务 ≥1 neutral 对照）。
