# 预实验协议摘要（protocol_pilot）

> 本文件是 `Prompt_V2.md`（v2.0，2026-10-08）的执行摘要，供仓库协作者快速对齐。两处冲突时以 Prompt_V2 为准，并在此登记修订。

## 1. 研究定位与边界

- **只研究**：H1a（前沿能力需求是否集中于少数步骤/类型）、H1b（可验证性是否比难度更能解释替换效应 ΔSR）、轻量"检查—重试/升级"机制探索（连接 H1 与 H2，**不等于**验证门控算法）。
- **不做**：LoRA 专用化、共形风险控制完整 H2、六维完整 H3、6 个月纵向观察、全部路由基线复现。
- **三类陈述必须区分**：协议正式设计 / 本预实验简化建议 / 尚待验证假设。后者只能以日志与数据支撑，不得提前宣称成立。

## 2. 核心变量

| 变量 | 定义 | 代码位置 |
|---|---|---|
| Y（任务成败） | 官方客观判定；记录模型判官参与情况 | configs/tasks.yaml + metrics |
| ΔSR | 同前置状态、同续写条件下 `SR(frontier) − SR(local)` | verifront/counterfactual/runner.py |
| type | 八类步骤语义标注，允许"无法唯一归类" | verifront/traces/steps.py |
| correct_step | 独立真值，与任务成败分开 | verifront/annotations/labels.py |
| checker_score | 单次检查输出（**不是** AUROC） | verifront/checkers/ |
| V（可验证性） | 独立标注样本上的判别力（AUROC），缺类记 NA | verifront/metrics/auroc.py |
| D（难度） | 双人盲评 1–5 级；不得用被研究小模型的错误率定义 | verifront/annotations/labels.py |

## 3. 阶段计划与门槛

| 阶段 | 规模 | 交付物 / 验收 |
|---|---|---|
| P0 | 3–5 个 SAB 任务 | environment.lock、任务日志、真实费用表；端到端可运行 |
| P1 | 20–30 轨迹；≥20 恢复锚点；试标 50–80 步骤 | 步骤手册、κ/覆盖率、恢复保真报告（试点目标恢复率 ≥90%） |
| P2 | 3–4 类步骤、80–150 候选输出 | 独立正确性标签、检查器判别力报告；无足够正负样本则**不报 AUROC** |
| P3 | 10–20 任务、50–100 替换实例 | 配对 ΔSR 与区间、恢复排除率、初步图景 |
| P4 | 25–30 任务、200–250 实例 | H1 预实验报告、正式协议草案、go/no-go |

**Go / Refine / Pivot / Stop 判据**见 Prompt_V2 §8.3；不以小样本 p<0.05 作为唯一扩大门槛，但恢复率与 κ 的工程门槛必须达标。

## 4. 关键设计约束（违者结果无效）

1. 三层表示（事件—动作—语义步骤）；动作级替换结果必须标注粒度，不外推为八类规律。
2. 对照组与处理组必须**同一前置状态 + 同一续写模型/工具/预算**；续写条件不一致的运行单列，不混入因果对照。
3. 替换点按预登记规则抽样（`reports/pilot/sampling_config.json`）；所有排除与恢复失败记录在案，不得静默删除。
4. 正确性真值独立于最终任务成败；禁止"运行无报错=科研正确"；禁止用同一套测试既定义真值又评价检查器。
5. 成本核算包含**替换后的全部续跑**，不只算替换步骤。
6. 版本锁定：仓库 commit、镜像 digest、模型 snapshot、评测版本全部记录；不得依赖浮动 `main`。

## 5. P0 必答清单（附录 A 摘录）

- [ ] SAB verified 数据与评测程序可获取，登记来源与版本
- [ ] OpenHands 兼容版本锁定（注意 V0→V1 迁移风险）
- [ ] 3–5 个轻依赖任务人工核查评分规则；标识使用模型判官的任务
- [ ] 前沿 Agent 跑通完整轨迹、产物、评分存档
- [ ] 1 个 7B–8B 模型在目标 GPU 上完成上下文与显存压测
- [ ] 5–10 个替换锚点确认可恢复
- [ ] 全流程费用/时长/存储/异常记录

## 6. 已知环境风险（Lab Compute 实测 2026-10-09）

- RTX 4090 24GB、96 核、251GB 内存、磁盘 256GB（**低于方案 B 的 300–500GB**，见磁盘纪律）。
- **容器运行时不可用（已定性，含证据链；复测脚本 `scripts/docker_capability_check.sh`）**：
  1. 宿主即容器：`/.dockerenv` 存在、cgroup 路径 `/docker/<id>`、PID 1 为 docker-init；
  2. 能力集为 Docker 默认集，**无 `CAP_SYS_ADMIN`** → 特权式 DiD 不可行；
  3. seccomp 过滤（mode 2）阻止 `unshare`（含 `CLONE_NEWUSER`）→ rootless Docker/Podman 不可行；
  4. `/dev/fuse` 不存在 → rootless overlay 亦不可行；宿主 `docker.sock` 未挂载；
  5. 实证：apt 安装 docker.io 29.1.3 后以 `--storage-driver=vfs --iptables=false --bridge=none` 启动 daemon 成功，但 `docker run hello-world` 在 `failed to register layer: unshare: operation not permitted` 处失败——镜像无法解包，任何容器均无法运行。
- **P0 替代评测路线（协议允许的偏差，须记录）**：conda/venv 固定环境直接运行 SAB 任务与官方评测脚本，以 `environment.lock`（pip freeze + commit + 镜像/数据版本）逐任务锁版本；报告与论文 Limitations 中如实声明"未使用官方容器化评测，环境可复现性由锁文件保证"。若平台后续提供特权容器或挂载 `docker.sock`，恢复官方评测并重跑关键子集核对。

## 7. 预实验完成时必答的 10 个问题

见 Prompt_V2 §11（baseline 是否真跑通、步骤是什么、状态能否恢复、正确性如何定义、可验证性能否测量、替换效应有无结构、可验证性 vs 难度、检查机制是否有效、全成本、是否进入正式实验）。P4 报告须逐项给出证据、失败案例与适用范围。

## 修订记录

- 2026-10-09 初始化仓库脚手架；实现 §10 模块结构与 §10.2 测试；Lab 环境探测结果记入 §6。
- 2026-10-09 P0 进展：SAB pinned `c26e151`（verified 版确认 2026-04-30 发布）；HF verified split（102 任务）已存 Lab；SharePoint zip 需浏览器手动下载（禁止二次分发）。OpenHands 路线判定不可用：主仓已改 TypeScript 应用，`OpenHands/benchmarks`（`405bae7`）中 SAB 仅存于 unmaintained legacy（V0、docker 绑定），V1 无 SAB → **执行层采用 VeriFront 自研 CodeAct-lite，评测采用 SAB 官方 conda 路线**（`run_eval.py` 内置，偏差已登记）。详单见 `configs/environment.lock.yaml`。
- 2026-10-10 P0 推进：verified zip 经用户 HF 转存获取并解压（1.7GB，仅存 Lab 本地，不入库）。SAB 仓库已迁址 `osunlp/`→`OSU-NLP-Group/`（commit 不变）。工程事实登记：(a) verified zip 无 `__init__.py`，包导入型金标程序需本地补齐（`models/` 等被 `listdir` 遍历的数据目录除外）；(b) 金标程序须以 `python -m benchmark.gold_programs.<name>` 于工作目录执行，评测脚本可直跑；(c) `scitools-iris` 需 `xxhash<3`；(d) Lab 实例重建，驱动 570.172.08→595.91.07，全部状态自仓库+工作区凭据重建。**P0 首轮 5 任务前沿扫描（gpt-5.5-2026-04-23，每任务 1 次，6 步预算）：87✓、45✓、29✗(8/16)、34✗(57/91)、60✗ → SR=2/5**；轨迹与 result.json 存档（runs/ 不入库），摘要入 `reports/pilot/p0_first_sweep.md`。暴露的流程风险：网关超时会孤儿化前台进程造成同任务重复运行 → 运行目录改用 pid-stamp，长任务一律后台执行。
- 2026-10-10 P1 启动：16 任务池经 4 轮 gold 复现检验定稿（judge 发现、biopsykit 钉 0.9.0、`__init__.py` 清理规则），配置 `configs/tasks_p1_pool.yaml`。计价：ChatAnywhere gpt-5.5 0.035/0.21 元每千 token（272K 阶梯内），聚合器 `scripts/aggregate_runs.py` 直出 SR/成本。首轮 27 run（P0 补跑 5 + 新任务 11×2）SR=18/32=0.5625；锚点挖掘定位 4 类分歧（34 过度工程、60 MFA/NVC 语义缺口、18 集群分组 CV、44 纪元边界差 1 分钟）。步骤标注手册 v1 + 60 步试标采样器入库。
- 2026-10-10 **污染事件与沙箱隔离（重要方法学修订）**：P1 首批轨迹审计发现两层评测泄露，全部旧 frontier run 判无效并隔离至 `runs_quarantined/`：
  (1) **视图泄露**——agent 工作目录的 `benchmark/` 符号链接暴露金标/评测/评分规则全树。32 条冻结轨迹中 17 条提及受保护路径、9 条含 canary 行（agent 实读了金标内容；87 的旧"成功"即此伪影）。修复（commit `27280d9`）：agent 阶段工作目录只含真实数据集拷贝（官方 SAB 视图），eval 阶段由 root 换入全树。
  (2) **沙箱逃逸**——净化后 agent 仍借**绝对路径** `/data/lab/...` 直读 gold（5 条轨迹证实，85 号 run 甚至读到 gold_results 并"validation: mismatches 0"；另有 1 条借 `../` 读取兄弟 run 产物）。修复（commit `0aaba0e`）：工作目录迁出 /data/lab（`/tmp/vf_w/<uuid>/wd`，uuid 不可猜、父链 0711、用后即删）；`/data/lab` 收权 0750；agent step 以 nobody 降权执行（env 白名单剥离 API key；`preexec_fn` 显式 setgroups([])——**subprocess(user=) 不清 supplementary group，子进程仍持 root 组权限可读 /data/lab，此坑被 e2e 探针测试捕获**）；mount namespace 不可用（§6），nobody 降权为唯一可行隔离层，写 Limitations。
  (3) **有效语料重置**：净化重跑（16×2 冻结 + hint 34/60×2）SR 仍 18/32 但构成重构——87 假成功转真失败、18 污染伪影转真成功、34 hint 干预 0/2→2/2 翻转、60 部分翻转 1/2、18 锚点被否（干净环境无 hint 亦过）、44 未翻转。据此试标集需以第三批（nobody 沙箱、36 条）语料再生；旧 A 侧标注作废。详见 `reports/pilot/p1_sanitized_rerun.md`、`reports/pilot/anchor_mining.md`。
  (4) **环境锁修正**：testbed 环境实为 root 混合解析（user-site 优先）——有效版本 pandas 2.3.3 / numpy 1.26.4 / matplotlib 3.7.5 / scipy 1.13.1，此前记录的 pandas 1.5.3 从未实际生效；nobody 与 root 解析一致性已用 PYTHONPATH 钉扎并验证。`environment.lock.yaml` 已补记。
