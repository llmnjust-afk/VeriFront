# 前置状态等价定义（state_equivalence）

对应 Prompt_V2 §4。目标：把"仅重放动作"升级为"前置状态等价"，使配对替换实验的两组从可验证的同一状态出发。

## 必须恢复的状态层

| 状态层 | 最小要求 | 验证方式 | 代码 |
|---|---|---|---|
| 文件系统 | 输入/生成文件、工作目录、关键中间产物一致 | 关键文件 SHA-256 清单比对 | `state/capture.capture_fs_manifest` |
| 运行环境 | 包版本、环境变量、种子、容器镜像、资源限制 | 环境摘要 manifest | `state/capture.capture_env_digest` |
| 会话/进程 | 必需 Python 变量、内存对象、服务状态 | 指定 probe 函数；必要时重启重演 | `PreState.process_probe` |
| Agent 可观察状态 | 可见消息、工具反馈、计划文本、工具历史 | 归一化后摘要比对 | `PreState.agent_context` |
| 外部工具与时间 | 网络资源、远端库状态、时间戳 | 固定/缓存依赖；不能控制则标 unsupported | `PreState.external` |

**`docker commit` 只覆盖容器文件系统主体，不是进程内存的通用快照**——不得当作免验证的兜底（Prompt_V2 §4.2）。

## 恢复策略

- **方案 A（首选，先测再用）：确定性重放**——从干净环境重执行前序动作，同时重建完整可观察对话历史与工具结果。
- **方案 B：受控检查点**——文件系统/可持久化工具状态做检查点；Python kernel 内存用该环境实际支持的会话持久化，或重新执行初始化与前序单元格。

## 非确定性差异的标准化规则

时间戳、临时路径等**不影响语义**的差异必须在**预先登记**的标准化规则内消除（`DEFAULT_NORMALIZATION_RULES`），不允许事后随意忽略。新增规则必须先登记再使用，并在报告中披露。

## 等价判定与验收

- `StateEquivalenceChecker.compare(pre, post)` 逐维返回 `match / mismatch / unsupported / error`；`files`、`environment`、`agent_context` 三维为必需维，任一 `mismatch` 即整体不通过。
- **验收门槛（工程目标，非统计保证）**：先导 ≥90% 锚点可恢复；正式扩规模前 ≥95%。
- 恢复失败按类型计数（文件缺失、哈希不一致、probe 缺失、上下文差异、外部依赖不可控），失败实例**不得静默删除**；主报告给出纳入/排除清单。
- 测试要求（§10.2）：故意扰动文件或上下文后，检查器必须**报失败而非误判成功**（见 `tests/test_state_equivalence.py`）。
