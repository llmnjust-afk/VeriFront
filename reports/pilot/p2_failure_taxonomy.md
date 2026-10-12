# P2a 失效机理分类学（初版 v0.1）

**依据** `VeriFront_P2_Research_Plan.md` §4.1 ｜ **数据** `p2_mechanism_annotations.csv`（455 run 逐条机理特征）｜ **生成脚本** `scripts/p2_mechanism_features.py`

---

## 1. 错误分类词典（自动层）

对每个 run 的接管步第一个 tool_result 的 STDERR 做正则分类（`edit_error_type`），多标签取首命中：

| 标签 | 正则/规则 | 对应 plan 错误类 |
|---|---|---|
| `dependency` | ModuleNotFoundError / ImportError | API/依赖误用 |
| `syntax` | SyntaxError / IndentationError | 语义或算法逻辑错误 |
| `name_attr` | NameError / AttributeError / TypeError / ValueError | 语义或算法逻辑错误 |
| `data_state` | FileNotFoundError / KeyError / IndexError / EmptyDataError | 数据/隐式状态误读 |
| `assert` | AssertionError | 验证反馈未使用（执行期） |
| `timeout` | Timeout / timed out | 执行环境异常 |
| `memory` | OutOfMemory / MemoryError / Killed | 执行环境异常 |
| `other_error` | 含 Traceback/Error 但未命中上述 | 待人工归类 |
| `no_code` | 接管步 parsed_action ∈ {none, final} | 协议失效 |
| `none` | exit_code=0 且无异常 | 执行通过（产物质量另判） |

**边界规则**（plan §4.1 原则）：
- `code` + exit=0 + 最终 Y=0 **不**自动等于"第 t 步能力失效"——需 P2a 人工层核对产物偏差与后续传播；
- `no_code`（final）不自动等于"过早终结"——需对照当时状态判断；
- stderr 缺失（qwen 若干 run 无 STDERR 块）按 exit_code 判。

---

## 2. 三层失效结构（首个机理发现）

**信号点 + 对照点合并的接管步崩溃率**（exit≠0 且有异常）：

| 臂 | 信号点崩溃率 | 对照点崩溃率 | no_code（信号/对照） |
|---|---|---|---|
| resample | 0% | 7% | 0% / 0% |
| mini | 11% | 12% | 6% / 8% |
| deepseek | 5% | 7% | 16% / 14% |
| **qwen** | **58%** | **58%** | 0% / 0% |

**解读**：
1. **执行级失效是 qwen 的模型级全局属性**（58% = 58%，与点位无关），不是信号步特异。错误构成全部为逻辑/接口类：ValueError 14、TypeError 8、NameError 6、KeyError 3（样例：`df.merge(on=列不存在)`、`grid_search.fit(形状不符)`、`json.dump(不可序列化对象)`、lambda 作用域 NameError），无依赖/环境类。
2. **mini/ds 走语义级路径**：崩溃率与 resample 基线（7%）同量级，其失效发生在"代码跑通但产物错误"层面——与臂级 SR 损失（mini 0.49/ds 0.55 vs resample 0.60）匹配。
3. resample 的 7% 崩溃为环境/偶发底噪。

**论文表述**：替换失效呈三层——基线偶发（~7%）、语义级（mini/ds：执行无异常但产物偏离）、执行级（qwen：近 6 成当场崩溃）。"每步撞上不同的墙"在 mini/ds 之间成立于语义层，在 qwen 上则叠加了一层全局执行短板。

---

## 3. 差中差口径（DiD，plan G1 定义 ΔSR = SR(替换) − SR(基线)）

| 臂 | sig SR | ctl SR | ΔSR_sig | ΔSR_ctl | **DiD（信号步额外损伤）** |
|---|---|---|---|---|---|
| mini | 22/36 (0.61) | 50/97 (0.52) | −0.20 | +0.00 | **−0.20** |
| deepseek | 23/38 (0.61) | 53/95 (0.56) | −0.21 | +0.04 | **−0.25** |
| qwen | 21/52 (0.40) | 无数据 | −0.41 | − | **NA（待补对照 run）** |

- mini/ds 的 DiD 干净确认步特异额外损伤：对照点 ΔSR≈0/+0.04，信号点 −0.20/−0.21。
- **qwen 无对照点 run**（复验仅覆盖信号点）→ P2b 必须补跑 qwen 对照臂（~10 非信号点 × 4 ≈ 40 run，本地推理 0 API 成本，仅 frontier 续跑 ≈20–30 CA），否则"跨类确认"的合并检验（p=0.0022/0.0001）无法剥离全局弱性成分。
- 合并检验与 DiD 的关系：合并 p 值回答"信号点上替换是否劣于基线"；DiD 回答"该劣化中有多大份额是信号步特异的"。论文应并列报告两者。

---

## 4. 信号点接管步后轨迹健康（qwen 修复悖论）

| 臂 | n | 接管步 exit≠0 % | 后续步执行失败均值 | 修改代码重试 % | 到达 final % |
|---|---|---|---|---|---|
| resample | 38 | 0% | 0.05 | 66% | 95% |
| mini | 36 | 11% | 0.06 | 53% | 97% |
| deepseek | 38 | 5% | 0.16 | 84% | 95% |
| qwen | 52 | 58% | 0.08 | 90% | 100% |

**qwen 修复悖论**：qwen 接管步 58% 当场崩溃，但后续由前沿模型执行时仅 0.08 次失败、90% 修改代码重试、100% 到达 final——执行错误几乎总被"接住"。**然而 qwen 臂信号点 SR 仍只有 0.40**：说明失效主体不在"代码崩了修不好"，而在**崩溃前/修复后产物已带偏**（错误中间状态、错误输出文件、错误统计口径）。这把"前沿依赖"的机理指向产物级语义质量而非执行韧性——需 P2a 人工层抽验（比对 qwen 修复成功 run 与 resample run 的中间产物差异）。

---

## 5. 待人工复核的优先样本（供标注层）

1. qwen 30 条崩溃 run 中"后续修复成功但 Y=0"的 run：产物偏差点定位（哪一步开始错）；
2. mini t60s6 0/6 全灭：6 条接管步代码 vs resample 5/7 成功代码的语义 diff（同输入、同前缀）；
3. ds t85s2 1/6 vs mini 6/6：同一 mini 稳步、ds 崩步的对照对；
4. t35s1 反例：ds 4/4 修复 + mini 2/4 修复的代码特征（何种"弱模型可解"的失败）；
5. 对照点 qwen：崩溃 58% 但 SR 0.40 ≈ 信号点——验证"修复后产物带偏"是否同样存在于对照点（若是，qwen 的信号点 ΔSR ≈ 全局弱性，步特异成分≈0；DiD 补跑后定量）。

---

## 6. 与 plan 的对齐

- §4.1 四层分析单位：自动层已覆盖"接管动作 + 执行结果 + 后续轨迹 + 终局"的结构化字段；**归因层**（错误是否为终局失败的直接原因）需人工标注，样本见 §5；
- §4.1 对照点要求：已纳入（§2/§3 的 ctl 列）；
- §4.2 特征标注：下一交付物（`p2_verifiability_codebook.md` + `p2_prediction_protocol.md`）。
