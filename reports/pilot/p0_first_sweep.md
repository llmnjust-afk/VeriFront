# P0 首轮前沿扫描（2026-10-10）

- 模型：`gpt-5.5-2026-04-23`（ChatAnywhere 中转，`api.chatanywhere.org/v1`）
- 执行层：VeriFront CodeAct-lite（6 步预算 / 单步 300s / max_tokens 8192 / temperature 0）
- 评测：SAB verified（zip 2026-04-30，commit `c26e151`）官方评测脚本，testbed 环境（见 environment.lock）
- 任务集：29、34、45、60、87（NeuroKit×2、BiopsyKit、ccobra、scitools-iris；全部客观判定，无判官）
- 每任务 1 次运行（非统计样本；P0 目的为管线验证 + 失败模式收集）

## 结果

| task | 域 | 状态 | 评测 | tokens(prompt/completion) | wall(s) | 备注 |
|---|---|---|---|---|---|---|
| 87 polynomial_fit | GIS | budget_exhausted | **1** (N/A) | 16,504 / 3,350 | 44 | 6 步均为代码，最后一步即正确产物，未发 final |
| 45 questionnaire | Psych | completed | **1** (12/12) | 23,518 / 4,960 | 55 | 首步报错后自修复 |
| 29 bio_eventrelated | Psych | completed | **0** (8/16) | 33,980 / 5,486 | 65 | 数值半数超容差 → P1 锚点候选 |
| 34 HRV_analyze | Psych | completed | **0** (57/91) | 15,169 / 8,802 | 80 | 列容差未达标 |
| 60 nvc_accuracies | Psych | completed | **0** | 25,525 / 3,600 | 41 | 产物结构不符 |

**SR = 2/5**（小样本基线，仅用于管线验证与锚点挖掘，不作结论）。

## 成本记录

- token 计量如上表（含 reasoning tokens 的模型按 completion 计）。
- USD 费用：TBD——中转站计价与官方价可能不同，待取得计价口径后回填；所有轨迹均存 token 数，可随时换算。

## 事故与修正

1. 前台长任务被网关 524 切断后遗留孤儿进程，与后续批次同任务并发 → 运行目录 pid-stamp 化；长任务一律 `background`。
2. verified zip 缺 `__init__.py`；补齐后 `python -m` 执行金标（详见 protocol_pilot §修订记录 2026-10-10）。

## P1 指向

- 失败任务的步骤级分析（29 的数值处理约定差异、60 的输出结构）将作为恢复锚点与步骤标注的首批素材。
- budget_exhausted-但-评测通过（task 87）提示"任务成败"与"轨迹终止形态"需分开报告（协议 §2 已区分 Y 与轨迹属性）。
