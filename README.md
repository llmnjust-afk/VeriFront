# VeriFront

可验证性驱动的科研 Agent 前沿能力需求分析与步骤级反事实实验——预实验（P0–P4）的实验控制代码库。

**协议唯一事实来源：** `Prompt_V2.md`（预实验方案 v2.0，2026-10-08）。本仓库只实现其 §10 规定的工程结构；所有科学主张以协议文档为准，预实验阶段不得提前宣称结论。

## 研究定位（摘自协议 §0）

- 主攻 **H1a**（前沿能力需求是否集中于少数步骤/步骤类型）与 **H1b**（可验证性是否比难度更能解释替换效应 ΔSR），外加轻量"检查—重试/升级"机制探索（非完整 H2）。
- 本次**不做**：LoRA 专用化、共形风险控制完整系统、六维完整 H3、6 个月纵向观察、全部路由基线。

## 仓库结构

```text
VeriFront/
├── docs/          协议摘要、步骤本体、状态等价定义
├── configs/       任务、模型、实验参数（YAML，P0 待填字段均为 null）
├── verifront/     实验控制代码
│   ├── agents/    前沿 API / 本地 vLLM 客户端、OpenHands 事件适配
│   ├── traces/    事件-动作-语义步骤三层表示与最小日志格式
│   ├── state/     前置状态捕获、重放与等价性检查
│   ├── counterfactual/  替换点预注册抽样 + 配对反事实执行器
│   ├── annotations/     步骤类型/正确性标签、Cohen κ
│   ├── checkers/  确定性独立检查器（schema/单测/重算/引文）
│   ├── metrics/   AUROC（缺类即 NA）、任务级聚类 ΔSR、全成本核算
│   └── analysis/  试点汇总报告与 go/refine/pivot 门槛
├── tests/         §10.2 要求的单元与集成测试
├── scripts/       smoke_test.sh（P0 冒烟）、run_pilot.sh
└── reports/pilot/ 可公开的结果摘要（原始日志不入库）
```

## 快速开始

```bash
python3 -m pip install -e ".[dev]"
bash scripts/smoke_test.sh      # 环境自检 + 全部单元测试
```

## 实现状态（对应协议 §10.1 优先级）

| 优先级 | 模块 | 状态 |
|---|---|---|
| P0 integration/smoke | `scripts/smoke_test.sh`、仓库/版本锁定字段 | 已实现；SAB/OpenHands 实际克隆与评测**待 P0 执行** |
| traces/event_export | `verifront/traces/` | 已实现 + 单测（OpenHands 字段映射需 P0 对真实事件流校准） |
| state/replay + equivalence | `verifront/state/` | 已实现 + 单测；`docker commit` 局限已显式建模 |
| counterfactual/replace | `verifront/counterfactual/` | 已实现 + 单测（真实模型接入待 API key） |
| annotations + checkers | `verifront/annotations/`, `verifront/checkers/` | 已实现 + 单测 |
| analysis + reporting | `verifront/metrics/`, `verifront/analysis/` | 已实现 + 单测（小样本边界如实报告） |
| 验证门控 / LoRA / 强基线 | — | 按协议明确**不在预实验范围** |

## P0 待办（需人工/密钥，见 docs/protocol_pilot.md 附录）

1. 安装或替代 Docker（当前 Lab 机器缺失，SAB 官方评测依赖容器）——先实测容器方案是否可用。
2. 克隆 SAB 与 OpenHands 并登记 commit SHA；获取 SAB verified 数据；锁定可运行版本。
3. 选 3–5 个客观评分、依赖轻的任务；跑通 前沿 Agent → 轨迹 → 官方评测。
4. 部署 1 个 7B–8B 本地模型（vLLM，bf16，并发 1、上下文 ≤32k 起步）并做显存/上下文压测。
5. 记录全流程费用/时长/存储/异常，形成预算表；不沿用任何未经实测的报价。

## 安全与合规

- 密钥只经环境变量（`FRONTIER_API_KEY` 等）注入，**永不入库**；`.gitignore` 已拦截。
- 不提交任务原始数据、模型权重、受限素材；公共仓库只提交脚本、索引与可公开摘要。
- 机器学习平台的访问令牌属于敏感凭据，仅存放在计算环境本地文件（权限 600），建议使用仅授权本仓库、可随时吊销的细粒度 token。
