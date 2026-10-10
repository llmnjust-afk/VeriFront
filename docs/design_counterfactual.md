# P1 反事实替换实验设计（v1，对齐 Prompt_V2 §4–§5）

日期：2026-10-10。上游输入：第三批无污染冻结矩阵（SR 17/32）、仲裁 gold 步骤标注
（16 critical_success / 11 critical_failure / 33 neutral）、步骤标注手册 v2（type κ=0.779）。

## 1. 实验问题与臂结构

在**同一前置状态**下比较两种第 t 步的生成者，其余步骤、工具与预算完全相同：

- **对照臂 `frontier_resample`**：第 t 步由前沿模型（gpt-5.5-2026-04-23，冻结配置）重新生成；
- **处理臂 `local_replace`**：第 t 步由小模型生成，第 t+1 步起恢复前沿模型（协议 §0.3.5：
  替换只发生在 t 步，后续执行条件相同）。

替换效应（任务级配对，协议 §1.2）：
`ΔSR_point = SR(frontier_resample) − SR(local_replace)`，每点 2 次重复。
Y = SAB 官方客观 eval（38 任务池内）。成本核算含替换后的全部续跑（协议 §0.3.7）。

对照性质说明：resample 臂同时充当 (a) 恢复保真的验收载体（前置状态重建后前沿能否
复现原 run 的成功率水平）与 (b) 替换效应的配对基线。

## 2. 替换点选择（步骤实例）

- **处理点候选**：gold 标注的 critical_success（成功 run，16 步）与 critical_failure
  （失败 run，11 步）步骤实例；critical_failure 点的预期是"小模型难以修复"或
  "前沿续跑可被小模型错误带偏"，critical_success 点的预期是"移除前沿决策即失去成功"。
- **对照点**：每任务 ≥1 个 gold neutral 步（匹配位置深度），用于校准 ΔSR 的噪声底。
- 同一任务的多个替换点观测**不独立**（协议 §1.1）；统计按任务聚类。
- 试点期只取 3 个任务（45、37、60），扩展期覆盖 16 任务 × 每任务 2–4 点。

## 3. 状态恢复：方案 A 确定性重放（协议 §4.2 首选）

第 t 步的前置状态由两层重建：

1. **可观察对话历史（消息层）**：从原始 `trace.jsonl` 确定性重建——
   `system = SYSTEM_PROMPT_TEMPLATE(max_steps, task_description, extra_context)`；
   `user("Begin. Output your first block.")`；随后对每个已执行步骤 i < t 依次追加
   `assistant(visible_agent_context)` 与 `user("EXECUTION RESULT [status]\nobservation")`
   （取原始 trace 文本，含 format_error/timeout/error 的原始观察）。**消息层与原始
   run 逐字节一致**（这是协议"重建完整的可观察对话历史、工具结果"的字面实现）。
2. **文件系统状态（执行层）**：在全新沙箱 workdir 中按序重放执行原始
   `step_01.py … step_{t-1}.py`（nobody 沙箱、同一 testbed 解释器、与冻结 run 相同的
   数据集视图）。第 t 步起的执行继续在该 workdir 进行。

### 保真验收（协议 §4.3）

- 每个替换点重放后记录：文件清单 + SHA256（对照原始 run 同名产物的 hash 集合）；
  前序步重放观察 vs 原始观察的**逐字一致率**与差异分类（时间戳类/随机性类/实质差异）。
- 工程门槛：试点期 ≥90% 替换点"重放可恢复"（文件集一致且无实质观察差异）；
  实质差异（如随机搜索产生的不同中间值）允许存在但必须归档，并在该点的解释中声明。
- 恢复失败（前序代码不可重放，如依赖已消失的外部状态）→ 该点记为 `unrecoverable`，
  不静默删除；主报告提供纳入/排除清单（协议 §4.3.4）。

## 4. 执行细节

- 步预算：总 12 步不变；重放消耗 0 步预算（是状态恢复，不是生成），第 t 步起
  按原 run 剩余预算继续（`remaining = max_steps − (t−1)`）。
- 沙箱：全部 step 执行沿用 nobody 降权沙箱（commit 0aaba0e）。
- 小模型接口：OpenAICompatClient 换 `model` 字段；试点用 API 小模型
  （gpt-5.2-mini 或 deepseek 系，定价入库），本地 Qwen3-8B（vLLM）就绪后作为主
  小模型重跑关键点（两套小模型结果分开报告）。
- 记录：cf run 独立 trace（`runs/sab_<id>/cf_<arm>/<stamp>/`），result.json 增加
  `cf_meta = {parent_run, edited_step, arm, model_at_edit, replay_fidelity}`。
- 每点 2 重复；编辑点执行失败（小模型输出不可解析）按 format_error 常规规则进入
  轨迹，不特殊豁免。

## 5. 分析计划

- 主量：点级 ΔSR（配对二值，2 重复）、按 gold role/type 分层的小模型成功率下降
  幅度（H1a 需求分布：哪些 step_type 的替换最伤 Y）。
- 任务级聚类不确定性：bootstrap by task（试点期仅描述性统计，不做显著性宣称）。
- 失败模式编码：替换点后续轨迹中"错误传播 vs 自愈"的定性编码（步骤标注手册沿用）。

## 6. 试点路线（本周）

1. **P1-CF0（管线打通）**：task 45 / step_01 替换点（无前缀重放，最简前置）。
   两臂 × 2 重复 = 4 run。验收：eval 正常出 Y、cf_meta 完整、小模型步可解析。
2. **P1-CF1（重放保真）**：task 37 / step_05 替换点（4 步前缀重放）+
   task 60 / step_08（7 步前缀）。保真验收按 §3。
3. 试点报告后扩至 16 任务替换点全集（估计 40–60 点 × 2 臂 × 2 重复 ≈ 160–240 run，
   预算 ≈ 250–400 CA ≈ $35–56；分批执行，每批后聚合审查）。
