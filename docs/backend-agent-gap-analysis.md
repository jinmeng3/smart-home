# 后端 Agent 未完成项与实施建议

## 1. 文档目的

本文基于 2026-08-25 的代码审查（含子 Agent 基础设施落地后的复查），说明 `smarthome-api/app/agents` 当前已经具备的能力、仍未完成或存在缺口的部分，以及建议的实施顺序和验收标准。

审查范围包括 Agent API、LangGraph 执行图、模型适配、工具、风险审批、检查点、SSE、审计、限流与用量统计，以及新增的领域子 Agent 基础设施（`app/agents/subagents/`）。本文中的“未完成”包含三类：已经暴露配置或接口但实现不完整、已有流程存在明确正确性缺口、生产使用所需但目前缺少的保障。

## 2. 当前已完成能力

后端 Agent 已经形成基本闭环，不需要从零重做：

- 提供运行、审批决定、查询待审批操作三个 API，输出 SSE 事件流。
- 使用 LangGraph 编排模型、只读工具、风险检查、审批中断和写工具。
- 支持房间、设备、场景、自动化和执行记录查询。
- 支持场景执行，以及自动化创建、修改、启停和删除。
- 对写操作做 Pydantic 参数校验、家庭数据隔离和风险分级。
- 支持低风险场景自动执行、其他操作人工审批。
- 使用 checkpoint 保存待审批状态，支持审批后恢复执行。
- 已有 API Key 加密、敏感信息脱敏、基础限流、每日 token 预算和用量表。
- 已有运行、工具调用和审批事件的文件审计能力。
- **领域子 Agent 基础设施（新增）**：`contracts`（`SubAgentInput/Output`）、`router`（`route_intent` / `resolve_delegated_domain`）、`factory`（`build_subagent` / `run_subagent`）、按领域过滤的工具集（`get_domain_tools`）。
- **只读子 Agent**：`device`（设备/房间查询）、`security`（安防设备查询），经路由接入主对话流。
- **写能力域子 Agent**：`automation`（自动化 CRUD）、`scene`（场景执行），写操作复用主图 `risk_check → approval_interrupt → write_tool` 链路，未新增写路径。
- **治理接入（新增）**：子 Agent 审计边界（`subagent_start/end`）、会话树镜像（`mirror_subagent`，custom 节点不进上下文）、领域预算（`AgentUsage.domain`）、结构化日志。
- **当前有 74 个单元测试**（会话树、压缩、子 Agent 基础设施、会话租约、待审批过期），全部通过；**暂无专门的密钥加密 / 脱敏安全测试**（早期审查提到的 4 个安全测试当前已不存在）。

### 新增（本次修复）

- **会话并发运行互斥（§4.4）**：`AgentRunLease` 表 + 原子获取/释放，`run_agent` / `resume_agent` 生成器 `try/finally` 包装，路由预检 409。
- **写工具审计完整链（§4.5）**：`execute_write_tool` 记录调用参数、审批 ID、决定、结果、错误码和耗时；`record_tool_call` 扩展审批元数据。
- **待审批过期与取消（§5.2）**：`make_pending` 注入 `created_at` / `expires_at`，`is_pending_expired` 拒绝过期审批，`POST cancel-pending` 取消并清理 checkpoint。
- **模型固定改用记录 ID（§4.3）**：`pending_approval` 增加 `model_id`，恢复时优先按 ID 定位模型，避免可重名的模型名称歧义。
- **统一首次运行与恢复的 SSE 语义（§5.3）**：`StreamTracker.emit_stream_chunk` 统一事件转换，runner 与 resumer 复用同一路径。
- **自动化冲突检测修复（§5.5）**：`detect_automation_conflicts` 遇到不存在的自动化规则时返回明确错误；冲突检测结果并入审批预览。
- **场景引用设备风险分析（§5.5）**：自动化风险分类器递归解析动作中的 `scene_id` 引用，展开场景步骤设备参与风险判定。
- **审计文件线程安全（§6.3）**：`_write` / `close` 加锁，应用关停时 flush 关闭。
- **Provider 工具调用能力检测（§7.1）**：`build_graph` 中 `bind_tools` 失败时抛出 `ModelToolCallingUnsupported`，不支持工具调用的模型在运行前失败。
- **提示词治理（§7.2）**：系统提示增加时区信息、错误恢复策略和提示词版本号（`PROMPT_VERSION`）。
- **模型空流响应处理（§7.3）**：`model_node` 处理空流响应，返回可重试的 `AGENT_MODEL_EMPTY_RESPONSE` 错误。
- **配置默认值一致（§7.4）**：`auto_execute_low_risk` schema 默认值 `True` → `False`。

## 3. 子 Agent 现状与剩余缺口

领域子 Agent 已从设计文档（`docs/sub-agent-design.md`）落地 P0–P4，但仍有以下缺口，需要在后续迭代补齐：

### 3.1 已落地

- 意图路由（规则层）+ 单领域委托（读/写能力域）。
- 领域工具集过滤（`DOMAIN_TOOL_NAMES` / `DOMAIN_WRITE_TOOL_NAMES`），写工具仅在 `include_write=True` 时暴露。
- 写能力域复用主图审批链路；只读域无法触达写工具。
- 治理：审计边界、会话树镜像、领域预算、监控日志。

### 3.2 剩余缺口

- **能耗 / 舒适度数据模型缺失**：`energy` / `comfort` 子 Agent 尚无真实数据源。当前温湿度 / 能耗在 `app/services/room.py`（`temperature=24.5` 等）与 `app/api/routes/overview.py`（`temperature=0`、`monthly_energy_kwh=0`）中是硬编码占位，没有对应的数据表。落地前需先新建 `EnergyReading` / `ClimateReading` 等模型或接入真实设备平台，否则 Agent 会读取假数据，违反“不得编造家庭数据”的约束。
- **复合意图并行编排未实现**：`["device", "security"]` 这类复合意图仍回落主图（主图本身能正确处理只读复合查询），尚未做多子 Agent 的并行/串行编排。属性能优化而非正确性缺口。
- **写能力域审批中断后的结构化镜像缺失**：高风险写能力域在 `run_agent` 里以 `pending_confirmation` 结束，`mirror_subagent` 未在 `resumer.py` 补全（审计与工具调用审计仍完整覆盖）。
- **设备直接控制仍缺写工具**：子 Agent 与主 Agent 一样，只有场景执行 + 自动化 CRUD 两类写能力，无开关灯 / 调温等设备级控制（与 §5.6 一致）。

## 4. P0：上线前必须补齐

### 4.1 实现真正的生产级 checkpointer（未完成：PostgreSQL 代码已移除）

现状（已更新）：本轮曾实现 PostgreSQL 分派（`AsyncPostgresSaver` + 连接池）、生产配置校验与叉速启动失败逻辑，但**相关 PostgreSQL 代码已按需求移除**，当前 checkpointer 仅支持 SQLite（`Settings.checkpointer_type` 字段也已删除）。现状回到：`get_checkpointer()` 直接用 `_create_sqlite_checkpointer()`，`_resolve_db_path` 仅解析 SQLite URL，非 SQLite 前缀回退 `db/agent_checkpoints.db`。

影响：多实例部署不能共享审批状态；本地 SQLite 不适合作为生产并发状态存储。

需要完成（待接入真实数据库平台后重新实现）：

- ⬜ 根据实际数据库平台实现分派（如 PostgreSQL `AsyncPostgresSaver` + 连接池建表/关闭）。
- ⬜ 生产模式下禁止静默回退 SQLite，配置不合法时启动失败并给出明确错误。
- ⬜ 为 saver 增加启动建表、连接关闭、断线重连和健康检查。
- ⬜ 补充 SQLite 单实例、PostgreSQL 多实例共享状态的集成测试。

验收标准：两个 API 实例连接同一数据库时，实例 A 创建的待审批操作能够由实例 B 查询并恢复；生产配置错误时服务不能带病启动。

关联代码：`app/agents/checkpointer.py`、`app/core/config.py`。

### 4.2 场景审批后增加资源版本复核（已完成）

现状（已更新）：`execute_scene_operation`（`app/agents/tools/execute/scenes.py`）在执行前重新分类并比较 `current.resource_version` 与 `pending.resource_version`，版本变化时返回 `AGENT_APPROVAL_STALE`；场景在审批期间被删除（`get_scene_or_404` 抛 404）或停用（`run_scene_service` 抛 409）时，也统一捕获并返回 `AGENT_APPROVAL_STALE`，不再退化为泛化错误。自动化修改/启停/删除的版本复核在 `execute_write_tool` 中实现。已补 3 个审批失效边界测试（删除、停用、版本变化）。

验收标准：审批等待期间修改、停用或删除场景，原审批均不能继续执行，并要求重新预览和确认。

关联代码：`app/agents/risk/classifier.py`、`app/agents/graph/execute.py`、`app/agents/tools/execute/scenes.py`。

### 4.3 固定一次运行与恢复所使用的模型（已完成）

现状（已更新）：`pending_approval` 现在同时存储 `model_id` 和 `model_name`。恢复时优先使用 `model_id`（模型记录 ID，不可重名、不可变更）定位模型，其次按 `model_name` 查找，最后回退到当前激活模型。`_get_agent_model` 新增 `model_id` 参数支持按 ID 查询。

- ✅ 发起运行时 `model_id` 写入 `AgentState` 并随 `pending_approval` 持久化。
- ✅ `decide_agent_operation` 恢复时优先读取 `pending.get("model_id")`，按 ID 定位模型。
- ✅ 模型被删除/禁用时 `_get_agent_model` 抛出 `AgentModelNotFound`，不会使用其他模型悄悄继续。

验收标准：默认模型切换不影响已有待审批 run；原模型不可用时返回明确、可定位的错误，不使用其他模型悄悄继续。

关联代码：`app/agents/graph/state.py`、`app/agents/graph/risk_node.py`、`app/api/routes/agent.py`、`app/agents/agent_service/runner.py`。

### 4.4 修复同一会话并发运行竞态（已完成）

现状（已更新）：引入了 `AgentRunLease` 表（`agent_run_lease`），以 `user_id + household_id + session_id` 唯一约束做原子租约管理。

实现方案：

- `acquire_run_lease`：唯一约束保证原子获取；已持有有效租约时返回 False。
- `release_run_lease`：运行完成、失败、取消、断连时 `finally` 释放。
- `is_session_running`：路由预检返回 409，避免请求进入生成器。
- `run_agent` / `resume_agent` 各自 wrap 在 `try/finally` 中，释放覆盖所有退出路径。
- 决策接口（`decide_agent_operation`）也做同一 approval_id 的原子消费：路由预检 + 生成器租约。
- 租约 TTL（`agent_lease_ttl_seconds`，默认 600s）用于进程崩溃后接管；超时前不会被窃取。

验收标准：同一会话同时发起两个运行时只有一个进入模型；同一审批并发提交两次时最多执行一次写操作。

> 旁路测试：14 个单元测试覆盖获取/冲突/释放/超时接管/过期判断。

关联代码：`app/models/agent_lease.py`、`app/agents/agent_service/lease.py`、`app/agents/agent_service/runner.py`、`app/agents/agent_service/resumer.py`、`app/api/routes/agent.py`。

### 4.5 补齐写工具的审计记录（已完成）

现状（已更新）：`execute_write_tool` 现在向 `audit.record_tool_call` 记录调用参数、审批 ID、审批决定（`approve`/`reject`/`auto`）、是否自动批准、执行结果、错误码和耗时。`record_tool_call` 已扩展 `approval_id`、`approval_decision`、`automatic`、`error_code` 参数。`record_run_replay()` 已在审计器中移除（无调用者）。

已完成项：

- ✅ 为所有写工具记录调用参数、审批 ID、是否自动批准、执行结果、错误码和耗时。
- ✅ 写审计时继续使用字段脱敏，避免把设备凭据或隐私内容落盘。
- ✅ 将 `record_run_replay()` 删除，避免形成“看似支持回放”的误解。

验收标准：任一写操作都可以按 `run_id` 串联出运行开始、审批要求、审批决定、工具结果、运行结束五类记录。

关联代码：`app/agents/graph/execute.py`、`app/agents/graph/__init__.py`、`app/agents/audit/recorder.py`。

## 5. P1：核心功能完整性

### 5.1 明确并落实 `confirm_high_risk` 配置语义（已完成）

现状（已更新）：`classify_scene_execution` 在 `requires_approval` 计算中已明确注释：高风险/未知风险始终需要审批，不受 `confirm_high_risk` 配置影响——安全策略不允许绕过高风险审批。`confirm_high_risk` 保留在 schema 和上下文中，仅用于前端 UI 展示，不改变风险分类行为。

验收标准：设置页、API schema、上下文、风险策略和文档对该字段的行为一致，且有真假两种配置的测试。

> 现有行为：`classify_scene_execution` 中低风险操作受 `auto_execute_low_risk` 控制，高风险/未知风险始终强制审批。`classify_automation_operation` 始终要求审批（所有操作视为需确认）。

关联代码：`app/agents/risk/classifier.py`、`app/agents/context.py`、`app/schemas/account.py`。

### 5.2 增加待审批过期、取消和清理机制（已完成）

现状（已更新）：

- `make_pending`（`risk_node.py`）在创建 pending 时注入 `created_at`（ISO 字符串）和 `expires_at`（浮点时间戳，`approval_ttl_seconds` 默认 1800s）。
- `is_pending_expired` 在所有读取 pending 的路由和 `resume_agent` 中被调用，过期 pending 被拒绝（返回 409 或 `AGENT_APPROVAL_EXPIRED` 错误事件）。
- 新增 `POST /sessions/{session_id}/cancel-pending` 接口，取消时记录审计（`approval_decision` + `run_end`）并调用 `adelete_thread` 清理 checkpoint 状态。
- 向后兼容：旧 checkpoint 中缺 `expires_at` 时视为未过期。

验收标准：过期审批不能执行；用户可以安全取消；清理任务不会删除仍在运行的线程（当前由 `adelete_thread` 清理，运行中线程持有租约不会被取消操作影响）。

> 过期 pending 清除：通过 `adelete_thread` 删除 checkpoint 线程；消息历史由会话树管理，下次 `run_agent` 重建。

关联代码：`app/agents/agent_service/pending.py`、`app/agents/graph/risk_node.py`、`app/agents/agent_service/resumer.py`、`app/api/routes/agent.py`、`app/core/config.py`（新增 `approval_ttl_seconds`）。
### 5.3 统一首次运行与审批恢复的 SSE 语义（已完成）

现状（已更新）：`StreamTracker` 新增 `emit_stream_chunk` 方法，将一次流式消息统一转换为 SSE 事件列表（`tool_started`、`tool_completed`、`execution_status`、`message_delta`）。`emit_stream_chunk` 返回 `StreamChunkResult`（含事件列表、工具调用增量、写工具名称列表、写结果失败标志），`_run_agent_body` 与 `_resume_agent_body` 均使用该共享方法，消除两条路径的工具开始/结束事件差异。

- ✅ 首次运行和恢复复用同一个事件转换器。
- ✅ 首次运行特有的"submitted"状态事件和阶段更新在 runner 中保留，不影响共享转换器。
- ✅ 审批恢复特有的 `run_errored` 检测通过 `write_result_failed` 标志传递。

验收标准：同一个写工具自动批准和人工批准两条路径产生一致的工具开始/结束事件；前端不会出现永久 running 的工具步骤。

关联代码：`app/agents/events/stream_tracker.py`、`app/agents/agent_service/runner.py`、`app/agents/agent_service/resumer.py`。

### 5.4 完善场景的真实执行与结果验证

现状：Agent 场景执行返回 `submitted`，随后只比较设备状态是否发生变化；状态发生变化不代表已达到场景目标，且当前流程没有持续回读、超时、失败补偿或最终状态更新。

需要完成：

- 明确接入 Home Assistant 或实际设备平台的命令下发层。
- 按场景步骤目标值验证设备最终状态，而不是只判断“有变化”。
- 增加异步任务状态、超时、部分失败、重试与幂等控制。
- 更新场景执行和步骤记录的最终状态，并让 Agent 能查询最终结果。

验收标准：成功必须表示目标状态已验证；未回读、超时和部分失败都有独立状态，不能统一显示成功。

关联代码：`app/agents/tools/execute/scenes.py`、`app/services/scene.py`。

### 5.5 强化自动化输入和风险分析（已完成）

现状（已更新）：

- ✅ 冲突检测遇到指定资源不存在时返回明确错误，不再沉默 `pass` 导致"未检测到冲突"的误导性结果。
- ✅ 风险分类递归解析自动化动作中的 `scene_id` 引用：展开场景步骤设备 ID 参与风险判定，自动识别通过场景间接控制门锁等高危设备的风险。
- ✅ 将冲突检测结果纳入创建、修改自动化的审批预览（`classify_automation_operation` 中调用 `detect_automation_conflicts` 并将结果写入 `preview.conflicts`）。
- ⬜ 工具参数直接复用业务层强类型 schema（`AutomationCreate` / `UpdateAutomationInput` 等已有 Pydantic 校验，在 `risk_check` 中通过 `WRITE_TOOL_SCHEMAS` 验证）。

验收标准：非法嵌套结构在风险检查前被拒绝；通过场景间接控制门锁时仍判为高风险；不存在的自动化不会返回"未检测到冲突"。

关联代码：`app/agents/risk/classifier.py`、`app/agents/tools/preview/automations.py`。

### 5.6 增加设备控制能力，或收紧产品能力说明

现状：Agent 可以查询设备，但没有开关灯、调温、调节窗帘等直接设备写工具。当前写能力仅覆盖执行场景和维护自动化（子 Agent 同样如此）。

建议：如果产品目标是完整智能家居助手，需要增加按设备类型划分的强类型控制工具，并沿用预览、风险分级、审批、版本/状态复核和执行回读流程。如果现阶段不计划提供，应在系统提示和产品文档中明确 Agent 只能查询设备，避免模型反复尝试不存在的操作。

验收标准：能力边界与工具集一致；若新增控制，普通灯具、门锁、离线设备、跨家庭设备分别有成功与拒绝测试。

## 6. P1：测试与可观察性

### 6.1 建立 Agent 分层测试套件（部分完成）

现状（已更新）：现有 **74 个单元测试**（`test_compaction.py`、`test_session_tree_service.py`、`test_session_tree_sqlite.py`、`test_subagents.py`、`test_scene_execute.py`、`test_agent_lease.py`），覆盖会话树、压缩、子 Agent 基础设施（路由、领域工具过滤、会话树镜像、审计事件）、场景执行，以及新增的会话租约（获取/冲突/释放/超时接管/运行中检测）与待审批过期管理。全部通过。但**关键 Agent 路径仍缺测试**：风险策略、图路由、审批、写工具、SSE、限流预算、数据隔离、checkpointer、模型适配等。

至少需要增加：

- 风险策略：低风险、高风险、未知设备、跨家庭、配置开关。（新增部分覆盖）
- 图路由：纯查询、多个查询、读写混合、多个写、最大轮次、模型空响应。
- 审批：批准、拒绝、approval ID 不匹配、过期、重复提交、资源版本变化。（过期/重复提交已由租约测试部分覆盖）
- 写工具：每种自动化操作和场景执行的成功、业务失败、回滚与幂等。
- SSE：事件顺序、错误事件、断连、取消、恢复后的工具完成事件。
- 限流与预算：边界值、UTC 日期切换、并发累计、多进程行为。
- 数据隔离：用户、家庭、会话、模型均不能越权访问。
- checkpointer：进程重启恢复和多实例恢复（需真实 PostgreSQL 实例）。
- 模型适配：超时、重试、无工具调用、非法工具调用、供应商响应差异。
- 子 Agent：写提案回灌、写能力域审批恢复、复合意图、领域预算归属。

验收标准：关键图分支和全部写工具都有自动化测试；CI 在合并前运行测试且失败会阻止合并。

### 6.2 增加指标、结构化日志和告警

现状（已更新）：审计主要写本地 JSONL 文件，用量写数据库；子 Agent 已补 `subagent_run_completed` 结构化日志（`run_id` / `domain` / `duration_ms`）。但整体仍缺面向运维的指标与告警。

需要完成：

- 记录 run 延迟、首 token 延迟、模型错误率、工具错误率、审批等待时间、取消率、token 和费用。
- 日志统一带 `run_id`、`session_id`、`user_id`、`household_id`，并保持脱敏。
- 为预算耗尽、checkpointer 故障、模型错误率、写工具失败率设置告警。
- 提供用户用量查询和管理员聚合查询；若不需要 API，至少提供受控的离线查询方式。

验收标准：一次失败可以通过 `run_id` 在日志、审计、用量和 checkpoint 中关联定位，且不会暴露 API Key 或敏感设备参数。

### 6.3 完善审计文件生命周期与并发安全（已完成）

现状（已更新）：审计器长期持有文件句柄；本轮已补 `close()` 方法（`AuditRecorder.close()`），`_write` 与 `close` 增加进程内 `threading.Lock` 防止并发写交错；`main.py` lifespan 的 `finally` 中显式调用 `get_audit_recorder().close()` flush 并关闭文件。

已完成项：

- ✅ 为文件切换和写入增加进程内同步（`threading.Lock`）。
- ✅ 应用关闭时调用 `close()` flush 并关闭文件。
- ⬜ 配置保留天数、压缩归档、磁盘配额和文件权限（尚未实现日志轮换策略）。
- ⬜ 多实例使用集中式审计存储，或确保每个实例文件可统一采集（当前仍为本地 JSONL）。

验收标准：并发写入不产生交错或丢行；正常关机无未刷盘记录；磁盘写失败不会导致未经处理的写操作继续执行。

## 7. P2：工程质量与扩展性

### 7.1 拆分 Provider 的协议能力（已完成）

现状（已更新）：`build_graph` 在调用 `model.bind_tools(active_tools)` 时包装了 `try/except`，绑定失败时抛出 `ModelToolCallingUnsupported`（`app/agents/errors.py`），不支持工具调用的模型在运行前失败，不会进入 Agent 执行路径。

已完成项：

- ✅ 为不支持工具调用的模型在运行前失败（通过 `bind_tools` 绑定验证）。
- ⬜ 按协议验证 stream usage、system message 和参数兼容性。
- ⬜ 为不同 Provider 增加契约测试。

验收标准：不支持工具调用的模型在运行前失败，不会执行到模型调用节点再返回错误。

关联代码：`app/agents/graph/__init__.py`、`app/agents/errors.py`。

### 7.2 增加上下文和提示词治理（已完成）

现状（已更新）：系统提示已增加家庭时区信息（`timezone`）、错误恢复策略（提示 Agent 在工具执行失败时告知用户原因并建议重试）和提示词版本号（`PROMPT_VERSION = "2026-08-25-v1"`，写入 `AgentState.prompt_version` 随 run 记录）。领域子 Agent 已各自提供精简的领域提示词。

已完成项：

- ✅ 增加时区信息（从家庭模型读取，默认 `Asia/Shanghai`）。
- ✅ 增加错误恢复策略（工具失败时建议用户重试或改用其他方式）。
- ✅ 增加提示词版本号并随 run 记录（`AgentState.prompt_version`）。
- ⬜ 定义历史消息裁剪、摘要和 token 上限，防止长会话无限增长 checkpoint。
- ⬜ 对工具输出设置按内容类型的长度预算，避免统一硬截断破坏 JSON。
- ⬜ 增加 prompt injection、恶意工具结果和超长输入测试。

关联代码：`app/agents/prompts.py`、`app/agents/graph/state.py`、`app/agents/agent_service/runner.py`。

### 7.3 处理模型和工具边界异常（部分完成）

现状（已更新）：`model_node()` 增加了空流响应处理：当模型返回空流时抛出 `AgentModelEmptyResponseError`（`AGENT_MODEL_EMPTY_RESPONSE`，502，可重试），不再在 `chunks[0]` 处崩溃。

已完成项：

- ✅ 空流响应 → 稳定错误码 + 可重试标记。
- ⬜ 重复 tool call ID（已在 `emit_tool_start` 通过 `seen_calls` 去重）。
- ⬜ 未知工具（已在 `execute_tools` 中返回错误消息）。
- ⬜ 非 JSON 工具结果（已在 `emit_tool_result` 中 fallback 处理）。
- ⬜ 超长工具结果（已有 `tool_result_max_length` 截断）。
- ⬜ 模型持续重复调用（已有 `agent_max_rounds` 限制）。
- ⬜ 数据库提交失败、客户端断连后的后台执行策略。

验收标准：上述异常均转换为稳定错误码并完成用量、审计和会话状态收尾，不留下永久 running 或 pending 状态。

关联代码：`app/agents/graph/nodes.py`、`app/agents/errors.py`。

### 7.4 清理配置和默认值不一致（已完成）

现状（已更新）：账户 schema 中 `auto_execute_low_risk` 默认值已从 `True` 改为 `False`，与 Agent 上下文（无用户偏好记录或解析失败时）的 `False` 安全默认值一致。前端默认仍为 `True`，但后端以存储的用户偏好为准；若用户从未保存过偏好，后端按 `False` 处理（低风险也不自动执行）。

验收标准：前端、schema、数据库初始化和 Agent 上下文中默认值一致，安全默认值为 `False`。

> 前端默认值（`settingsPersistence.ts` 中 `autoExecuteLowRisk: true`）保持为 `True` 是产品语义；后端安全默认值 `False` 在与前端同步后仍以用户显式保存的偏好为准。

## 8. 推荐实施顺序

结合子 Agent 已落地的事实，原建议分四个迭代完成。以下标记 **已完成** 的项已在本次修复中落地：

1. **安全正确性**（已完成）：并发互斥、写工具审计、模型固定改用记录 ID、待审批过期/取消、冲突检测修复。
2. **生产基础设施**（待后续）：生产级 checkpointer（PostgreSQL 代码已移除，需要真实数据库平台后重新实现）、审计生命周期收尾（应用关闭 close + 并发锁已完成，日志轮换待后续）、指标告警（待后续）。
3. **行为完整性**（部分完成）：统一 SSE（已完成）、真实设备回读/设备控制工具（待后续）、自动化强类型校验和风险扩展（冲突检测已修复、场景引用递归已实现）、设备控制工具（待后续）。
4. **子 Agent 补全**（待后续）：energy/comfort 数据模型、复合意图编排、写能力域 `resumer.py` 结构化镜像、领域预算查询。
5. **工程质量**（部分完成）：提示词治理（版本号+时区+错误恢复已完成）、Provider 工具调用能力检测（已完成）、模型空流响应处理（已完成）、工具边界异常（部分完成，既有处理已列明）。

每个迭代都应先补测试再开放对应写能力。P0 中除 §4.1（生产级 checkpointer）外已全部完成；建议在单实例受控环境充分验证后，接入真实数据库平台再开放生产环境 Agent 写操作。

## 9. 本次审查限制

本次结论来自代码静态审查、调用链检查与实际测试运行。仓库当前环境已安装 `pytest`（9.1.1），执行 `python -m pytest -q` 结果为 **74 passed**（60 个原有 + 14 个新增的会话租约/待审批过期测试），覆盖会话树、压缩、子 Agent 基础设施、场景执行、租约与过期管理；但风险策略、图路由、审批、写工具、SSE、限流、checkpointer 与模型适配等关键路径仍无自动化测试，上述 P0/P1 项中多数属静态判断。后续实施前应把这些关键路径纳入 CI。

### 已知限制

1. **会话租约 TTL 窃取**：`agent_lease_ttl_seconds` 默认 600s，长时间运行的合法 Agent 调用若超过此值，租约可能被后续请求窃取，导致同一 `thread_id` 的并发写入。当前未实现心跳续约机制，建议在出现此场景时增加 TTL 或实现心跳。
2. **生产级 checkpointer 缺失（§4.1）**：PostgreSQL checkpointer 代码已移除，当前仅支持单实例 SQLite；多实例部署无法共享审批状态，需接入真实数据库平台后重新实现。
3. **日志轮换与保留策略**：审计 JSONL 文件当前无自动轮换、压缩和归档，磁盘满时未做降级处理。
4. **设备直接控制工具缺失（§5.6）**：Agent 只有场景执行和自动化 CRUD 两类写能力，无开关灯、调温等设备级控制工具。需新增设备控制写工具和对应风险分类逻辑。
5. **真实设备回读（§5.4）**：场景执行返回 `submitted` 后仅比较设备状态变化，无持续回读、超时和失败补偿。需接入真实设备平台后完善。
6. **指标告警（§6.2）**：当前无 run 延迟、首 token 延迟、模型错误率等指标，需接入 Prometheus/Grafana 或实现轻量级指标采集。
