# VeriFront 主文骨架（Nature Machine Intelligence, Article）

**状态**：骨架 v0.1（数字锚点均已对照 repo 报告核实）｜ **成本记录**：≈767 run / ≈746 CA（≈$105）｜ 数据可用性：全部结果可由 `scripts/p2_reproduce_tables.py`、`p2_mechanism_features.py dod`、`p2_scan_stats.py`、`p2c_m0m1.py` 一键复现

---

## 标题（候选）

1. **Step-level counterfactual replacement reveals where scientific-code agents depend on frontier models**（首选：方法+发现双承诺）
2. Verifiability profiles predict step-level model dependence in scientific agents
3. Dissecting frontier-model dependence of scientific agents by step-level replacement

## 摘要草案（~200 w，unstructured）

Scientific agents built on LLMs fail opaquely: task-level pass rates cannot locate *where* capability is required. We introduce **step-level counterfactual replacement**—surgically substituting a frontier model with cheaper replacements at individual agent steps while holding context fixed—and apply it to scientific computing agents executing 38-odd multi-step data-analysis tasks. Across 767 controlled runs spanning four edit models (frontier resampling, two API-tier models, and a 14B open-weights model), replacement damage concentrates at a minority of steps; a 14B model matches or exceeds frontier performance at most inspection/verification steps yet collapses at specific deliverable-producing steps. Mechanistically, failures split into protocol lapses (no code emitted), semantic errors, and model-idiosyncratic error families, and structured feedback partially repairs them (+0.21 success rate at frontier steps) whereas naive step-splicing (suffix takeover) amplifies damage. Finally, two annotators blind to outcomes code seven verifiability features of each step from pre-registered materials; these features independently predict step-level replacement success under task-level cross-validation (ΔRMSE −0.04, Δρ +0.17 over controls), supporting verifiability as a design principle for allocating frontier capability. Our framework turns "which model for which step" from anecdote into measurement.

## 正文叙事弧（五步）

1. **问题**：任务级评估掩盖步级依赖；黑盒"换小模型会坏在哪"无人测量。
2. **方法**：步级反事实替换协议（parent 轨迹冻结、上下文保持、4 臂对照、客观判定）。
3. **发现 1（P2a）**：伤害集中于少数步骤（DiD：qwen −0.71 / ds −0.25 / mini −0.21）→ 三层失效分类。
4. **发现 2（P2b）**：全步剖面 + 机制干预（结构化反馈修复、后缀接管放大、8B→14B 不消除失效）。
5. **发现 3（P2c）**：双盲可验证性特征预测步级可替换性（M1 > M0，预注册判定通过）→ 设计原则。

---

## Results 小节与数字锚点

### R1「Replacement damage concentrates at identifiable steps」（P2a）

- 锚点：705 in-point runs；38 点实例 × 4 臂；信号点 6 个
- DiD 表（p2_did_table.md）：pooled qwen **−0.71**、ds **−0.25**、mini **−0.21**；common-set（10 共享对照）qwen −0.63 / ds −0.27 / mini −0.24（排序一致）
- 失效机理矩阵（p2_mechanism_matrix.md）：信号点上 qwen `other_error` 25/52 独有错误族；ds/mini `no_code`（协议失效）为主；resample 近乎零错
- 统计口径：Fisher 精确 + BH-FDR；分层 CMH（12 能力依赖步为层）

### R2「Full-step profiles separate healthy, capability-dependent, and cliff steps」（P2b 扫描）

- 锚点：193 scanned runs，t40/t60 两 parent × 12 步 × 4 臂剖面（p2_scan_stats.md T1/T2）
- 步分类：healthy（resample≈1）/ capability-dependent / cliff（resample=0）
- 42 步-臂逐点检验 BH-FDR q<0.10 = **0** → 步级单点功效不足，聚合证据（DiD、分类学、干预）承担推断 → 这是 R2→R3 的叙事桥梁

### R3「Mechanism interventions: structured feedback repairs, naive splicing amplifies」（P2b 干预）

- 反馈干预（p2_feedback_intervention_results.md）：resample 结构化 0.75 vs 裸重试 0.54（**+0.21**）；mini 0.42 vs 0.33；触发率结构化 1/12 vs 裸重试 3/13
- 后缀接管（p2_suffix_analysis.md）：mini t40s4 −0.19、t60s4 **−0.38**（切片拼接比整步替换更糟 → 步级依赖非局部可拼接）
- 14B 复验（p2_q14_analysis.md）：池化 8B 0.37 → 14B 0.45，Fisher p=0.610；6 信号点 2 修复 / 2 持续 / 2 新失效 → **模型规模不消除步级失效**
- 协议重试（p2_sec54_analysis.md）：budget_exhausted 重执行 8/8 完成、终态成功率 0.50 = 对照 0.50 → 预算耗尽非失败终点（诚实报告）

### R4「Blind-coded verifiability features predict step-level replaceability」（P2c）

- 双盲标注：38 点 × 7 特征；κ：F2 **0.83**、F7 **1.00** 通过；其余 <0.6 → 预注册澄清 + 17 处人工裁决（值域 {0,.5,1,1.5,2}）；冻结时间戳先于解盲（f6c05f2）
- M0/M1（p2c_m0m1_report.md）：134 观测 × LOTO（14 任务），固定 α=1.0：ΔRMSE **−0.036**、Δρ **+0.165**、ΔAUROC +0.069 → **支持 H2**（预注册双标准）
- GBM 敏感性同向；增益集中于探查/核对步（F1 区分探查步 vs 产物步）；qwen 增益被臂指示吸收；F5 弱维度如实记录
- 功效边界：38 点 < 60 点目标 → 方向性结论（Limitations 主项）

---

## 图表清单（Main 4 图 + SI）

| 编号 | 内容 | 数据源 | 状态 |
|---|---|---|---|
| **Fig 1** | 框架总览：parent 轨迹 → 步选择 → 4 臂替换 → 逐臂判定 → 特征盲标注 → 预测 | 概念图 | ❌ 需绘制（image_generate 或矢量重绘）|
| **Fig 2** | 全步剖面：t40/t60 × 12 步 × 4 臂 SR 热图/点线 + 步分类色带 | p2_scan_stats.md T1 | ⚠️ 有探索版 `p2_scan_profile.png`，需出版级重绘 |
| **Fig 3** | 机制证据三联：(a) DiD 条形（3 臂 × 2 口径）(b) 信号点失效机理堆叠条 (c) 反馈干预 vs 后缀接管效应森林图 | did/mechanism/feedback/suffix 四表 | ❌ 需绘制 |
| **Fig 4** | 预测结果：(a) M0 vs M1 LOFO RMSE/ρ (b) 逐臂改善条形 (c) Ridge 系数 | p2c_fold_predictions.csv | ❌ 需绘制 |
| SI Fig S1 | 信号点四臂对比（已有 `p2_fig_signal_points.png`）| T3 表 | ✅ 可直接用/微调 |
| SI Fig S2 | 三层失效分类图（`p2_fig_tiers.png`）| | ✅ |
| SI Fig S3 | 14B vs 8B 逐点复验 | q14 表 | ❌ 可选 |
| **Table 1** | 38 点 × 4 臂主表（SR + Wilson CI + 角色/层）| T2 表 | ✅ 已有底稿 |
| SI Table | κ 报告 + 裁决记录 + merged 特征分布 | annotation/ | ✅ |

绘图规范：viridis/Okabe-Ito 色板、误差条用 Wilson 95% CI、colorblind-safe、每图完整句 caption。

---

## Methods 清单（写作时逐条对齐 repo 资产）

1. Agent 骨架与任务域（SAB、verified.parquet、12 步预算、客观判定器）
2. 反事实替换协议（parent 冻结、上下文保真、4 臂定义、温度 0、沙箱 nobody 降权）
3. 信号点选择与对照点定义（信号点 6 + 对照 32；防循环论证声明）
4. 全步扫描与干预实验（扫描/反馈/后缀/14B 参数）
5. 盲标注协议（材料生成机检、双盲、κ、澄清二轮、裁决值域、冻结时间戳、A 侧污染披露）
6. 预测协议（M0/M1 定义、LOTO、固定超参、预注册判定、GBM 敏感性）
7. 统计（Fisher+BH-FDR、CMH、Wilson CI、功效声明）
8. 伦理/数据/代码可用性声明

## Limitations（预埋）

- 单一 agent 骨架、单任务域（SAB）、38 点方向性功效；F2 为 proxy；A 侧为 AI 助手的残余污染风险（敏感性分析待补：剔除 F5/F6 极端点重算）；跨域外推测试未完成（revision 弹药）

---

## 写作任务分解（下一步）

1. [ ] Fig 1 框架概念图（image_generate → 矢量重绘）
2. [ ] Fig 2/3/4 出版级 matplotlib（数据脚本直接出图）
3. [ ] Results 四小节初稿（本骨架数字锚点 → 正文）
4. [ ] 文献检索与 refs.bib（Nature style，50+，近 2 年为主）
5. [ ] Intro/Abstract/Discussion 初稿
6. [ ] Methods（对齐 repo 报告）
7. [ ] LaTeX 组装（nature 模板）+ 编译
