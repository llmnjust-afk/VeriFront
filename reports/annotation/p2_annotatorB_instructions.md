# 标注者 B 正式交付说明（v2 材料最终版）

**生成日期**：2026-10-14 ｜ **验收基准**：GitHub `llmnjust-afk/VeriFront` main 分支 commit `3b272f3` 之后的下一个含本文件的 commit（以最新 main 为准；核对 `git log -1 --format=%H`）

## 一、领取清单（只有这三样 + 一份疑问登记表自建）

| 文件 | 校验特征 |
|------|---------|
| `reports/annotation/blind_materials_v2.md` | 头部标题 "Blind Annotation Materials (v2)"；38 个 POINT；每个 STEP-CODE 块含**实际代码正文**（长度 101–22322 字符，绝无仅 `step_XX.py` 文件名的块）；无 `frontier`/`resample`/`local_replace` 字样 |
| `reports/pilot/p2_verifiability_codebook.md` | 首行标题含 **"Codebook v1.2，已冻结"**；文末有 v1.1 与 v1.2 两段变更日志 |
| `reports/annotation/p2_blind_template_annotatorB.csv` | 38 行 × 9 列，point_id 与材料逐点同序；F1–F7 与 rationale 留空待填 |

⚠️ 任何与本表校验特征不符的副本（例如标题仍为 v1.0/预注册草案、STEP-CODE 只有文件名）一律是**过期文件**，退回并从仓库 main 重新获取。

## 二、标注任务

按 `blind_materials_v2.md` 中 POINT 1–38 顺序，逐点对照 Codebook v1.2 §1 填写模板 CSV：

- **F1–F6**：只能填 **0 / 1 / 2**（原始评分；小数仅允许出现在后续仲裁产物，B 独立标注阶段禁止填 0.5/1.5）
- **F7**：只能填 `code_script` / `tool_call_only` / `analysis_text` / `mixed` 四者之一
- **rationale**：**每个 POINT 一条综合证据句**（方案 A），须引用该点材料中的具体证据，能解释主要取值；个别维度的特殊理由可写入"维度: 理由"的分号列表
- **拿不准**：分值**留空**（绝不填 0 当占位），同时在自建的 `annotatorB_questions.md` 里登记，每条含：`point_id`、维度、看到的证据、具体疑问

## 三、判定纪律（Codebook v1.2 已固化，要点重申）

1. 只依据材料可见证据；**材料未显示 ≠ 不存在**——不得凭"任务背后可能有隐藏评测器"抬高 F2，也不得把"未观察到反馈"推断为"确实没有"后乱给 F3/F4（拿不准就留空 + 登记疑问）
2. F5 判定仅用当步代码可见引用与 OBS 依赖证据（材料不含消息上下文摘要，这是统一口径而非材料缺陷）
3. F6 是对"结构性可恢复性"的事前判断，不猜测后续步骤实际发生了什么
4. 不判断"该步是否依赖前沿模型"（防循环原则）；不接触 A 侧任何文件、`reports/pilot/` 实验报告、`cf_points.json`、任何替换实验数据

## 四、交回

一个填好的 `p2_blind_template_annotatorB.csv` + 一个 `annotatorB_questions.md`（如有疑问）。之后由流程方计算 F1–F6 加权 κ、F7 非加权 κ，组织仲裁（F1–F6 ≤1 级取均值，值域 {0,0.5,1,1.5,2}；F7 类别共识）。
