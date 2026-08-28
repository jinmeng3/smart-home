# 基于前端界面的 Agent 功能缺口分析（后端验证版）

> 本文档已按照用户要求，于 2026-08-25 重新对照后端全部代码进行验证。**所有关于后端能力的陈述均来自实际代码，包含具体文件路径、函数名和行号引用**，而非基于前端假设或文档推测。

## 1. 文档目的与验证方法

### 目的

本文从 `smarthome-web` 已经展示给用户的入口、按钮、状态卡片、设置项和推荐提示词出发，反向检查 Agent 端到端能力是否真正完成。

审查重点回答三个问题，且**每个答案必须有后端代码佐证**：

- 前端已经出现的 Agent 功能，后端是否有对应实现；
- 前端向用户暗示的能力，后端是否存在对应工具和数据模型；
- 前后端契约是否闭环（SSE 事件、REST API、类型定义）。

### 验证范围与后端代码基线

本次验证覆盖以下后端模块（全部来自 `smarthome-api/app/`）：

| 模块路径 | 作用 | 关键文件 |
| --- | --- | --- |
| `agents/` | Agent 引擎核心 | `context.py`, `prompts.py`, `graph/`, `tools/`, `risk/`, `agent_service/` |
| `agents/subagents/` | 子 Agent 编排（新增） | `router.py`, `factory.py`, `contracts.py`, `domains/` |
| `agents/events/` | SSE 事件系统 | `stream_tracker.py`, `events.py` |
| `api/routes/agent.py` | Agent REST API | `agent.py` |
| `api/routes/chat.py` | 对话 API | `chat.py` |
| `session_tree/` | 会话树存储 | `session/`, `compaction/` |
| `compaction/` | 上下文压缩编排 | `engine.py`, `summarize.py`, `prompts.py` |
| `models/` | 数据模型 | `chat.py`, `device.py`, `scene.py`, `automation.py`, `user_preferences.py` |
| `schemas/` | Pydantic 校验 | `agent.py`, `sse.py` |

本次验证日期：2026-08-25。

### 验证结论速览

| 状态标签 | 含义 |
| --- | --- |
| ✅ 已完成 | 后端功能完整实现，前后端闭环 |
| ⚠️ 部分完成 | 后端有实现但存在缺口 |
| ❌ 未完成 | 后端缺少对应工具或数据模型 |
| 🔴 已修复（本次） | 此前标记为缺口，本次验证确认已修复 |

---

## 2. 总体结论

**后端已实现的核心能力：**

- Agent 运行引擎（LangGraph 状态机）：`app/agents/graph/` — 包括 `build_graph`、`should_continue`、`risk_check`、`approval_interrupt`、`tool_router` 等完整节点链
- 5 类写工具审批链路（场景执行 + 4 类自动化操作）：`app/agents/tools/__init__.py:10-16` 定义 `WRITE_TOOL_SCHEMAS`
- 11 类查询（只读）工具：`app/agents/tools/__init__.py:20-205` 中 `get_household_tools` 注册
- 3 类预览工具（场景预览、自动化变更预览、冲突检测）：同上
- 会话树形存储 + 上下文压缩：`app/session_tree/` + `app/compaction/`
- SSE 事件流（8 种事件类型）：`app/agents/events/stream_tracker.py`
- 子 Agent 基础设施（意图路由、领域工厂、只读/写能力域）：`app/agents/subagents/`
- 对话模式（跨轮记忆、按会话持久化）：`app/api/routes/chat.py`
- 语言/详细程度/自动执行偏好接入 system prompt：`app/agents/prompts.py:39-98`
- 审批恢复、重新生成、停止生成、状态查询等 REST API：`app/api/routes/agent.py`

**后端尚未实现的能力（前端已展示但后端无对应）：**

1. 语音输入（无音频 API）
2. 设备直接控制（无 `switch_light`/`set_temperature` 等写工具）
3. 能耗数据查询（无 `energy`/`consumption` 数据模型）
4. 全屋巡检（无 `inspect_household_health` 聚合工具）
5. 家庭日程/安防事件管理（无 `schedule`/`security_alert` 数据模型）
6. `confirm_high_risk` 偏好被解析（`app/agents/context.py:72-73`）但未被风险分类器使用（`app/agents/risk/classifier.py:261-264` 明确注释安全策略不允许绕过高风险审批）

---

## 3. 前端能力与实际完成度（后端验证版）

| 前端能力 | 后端验证状态 | 后端代码出处 | 主要问题 |
| --- | --- | --- | --- |
| Agent 流式对话 | ⚠️ 部分完成 | `app/api/routes/agent.py:84-151` POST `/runs`；`app/agents/agent_service/runner.py`；`app/agents/events/stream_tracker.py` | 首次运行和审批恢复均可消费 SSE；缺少断线续传和严格完成态处理 |
| 普通对话模式 | ✅ 已完成 | `app/api/routes/chat.py` 对话模式 POST `/api/chat/completions`；`app/services/chat.py` 跨轮记忆；`ChatSession.mode` 字段持久化 | 前端按 `agentMode` 分流；后端回放完整历史 |
| 模型选择 | ✅ 已完成 | `app/api/routes/agent.py:207-215` 审批恢复固定原模型；`ChatSession.model_name` 字段 | 选择模型只影响当前会话/run，不修改全局激活模型；审批恢复固定使用原模型 |
| 工具执行步骤 | ✅ 已完成 | `app/agents/events/stream_tracker.py` `emit_execution_status`/`emit_execution_result`；`app/agents/graph/execute.py` 写工具执行 | 首次运行和恢复审批后的 SSE 均正确消费；`execution_status` 事件已发送 |
| 场景执行审批 | ✅ 已完成 | `app/agents/risk/classifier.py:222-298` 场景风险分类；`app/agents/graph/risk_node.py:100-104` 场景风险判定 | 家庭 ID 正确、SSE 已消费、审批卡正确展示——端到端闭环 |
| 自动化变更审批 | ✅ 已完成 | `app/agents/risk/classifier.py:39-219` 自动化风险分类；`app/agents/tools/execute/automations.py` 创建/更新/启停/删除 | 后端 5 类写工具均支持并返回判别式 preview；前端识别 `kind` 并展示自动化专属字段 |
| 待审批恢复 | ✅ 已完成 | `app/api/routes/agent.py:154-225` POST `/sessions/{id}/decisions`；`app/agents/agent_service/resumer.py` | 首次运行后正确显示 pending 卡片，批准后消费 SSE 并更新状态，拒绝后显示最终回答 |
| 停止生成 | ✅ 已完成 | `app/api/routes/agent.py:385-397` GET `/sessions/{id}/run-status`；`agent_usage` 记录 `status`/`phase` | 保留部分回答与步骤、区分阶段反馈；后端提供按会话状态查询 |
| 重新生成 | ✅ 已完成 | `app/api/routes/agent.py:311-382` POST `/sessions/{id}/regenerate`；`_extract_history_before_user` 提取历史；checkpoint 回退 | 复用旧用户消息、覆盖旧助手回复；Agent 模式回退 checkpoint 不重放写操作 |
| 历史会话 | ⚠️ 部分完成 | `app/services/chat.py` 消息持久化 | 多处错误被静默吞掉；待审批前后的助手内容可能与后端历史不一致 |
| 语音输入 | ❌ 未完成 | 后端无音频/语音相关 API | 按钮没有点击处理、录音、转写或权限流程 |
| 全屋巡检 | ⚠️ 部分完成 | `app/agents/tools/query/devices.py` 仅有 `list_devices`/`get_device` 查询工具 | 无 `inspect_household_health` 聚合巡检工具，无规则化结论和告警处理 |
| 节能建议 | ❌ 未完成数据闭环 | 后端无 `energy`/`consumption` 数据模型（grep 未命中任何相关 ORM 模型） | Agent 无能耗数据工具；右侧能耗值为前端固定值 |
| 回家联动设置 | ⚠️ 部分完成 | `app/agents/tools/execute/automations.py` 可创建自动化；`app/agents/tools/preview/automations.py` 冲突检测 | 可创建自动化，但时间语义、冲突预览、审批卡和执行结果展示不完整 |
| 设备直接控制 | ❌ 未完成 | `app/agents/tools/__init__.py:10-16` `WRITE_TOOL_NAMES` 只有 scene + automation 操作，无 `switch_light`/`set_temperature` 等设备控制写工具 | Agent 只能查询设备，不能直接开关灯、调温、控制窗帘或安防设备 |
| Agent 高级设置 | ⚠️ 部分完成 | `app/agents/context.py:69-76` 解析 `autoExecuteLowRisk`/`confirmHighRisk`/`language`/`detailLevel`；`app/agents/risk/classifier.py:261-264` 安全策略不允许绕过高风险审批；`app/agents/prompts.py:31-36`/`27-28` 语言与详细程度已接入 | `auto_execute_low_risk` 已参与风险判定、语言与详细程度已接入 system prompt；`confirm_high_risk` 被解析但未被风险分类器使用 |
| 任务上下文侧栏 | ⚠️ 部分完成 | 后端无结构化 `resource_type`/`resource_id` 在工具结果中返回 | 多数内容来自前端本地状态，缺少后端结构化受影响资源和真实进度 |

---

## 4. P0：修复现有审批和执行闭环

### 4.1 修正审批请求中的家庭 ID

**状态：🔴 已修复**

**后端验证：** `app/api/routes/agent.py:154-167` 中 `decide_agent_operation` 接收 `AgentDecisionRequest`（`app/schemas/agent.py:23-26` 定义 `household_id: int = Field(gt=0)`）。`agent_context()`（`app/agents/context.py:34-53`）校验用户是否属于该家庭，不匹配时返回 403。同时校验 `session.household_id` 与请求的 `household_id` 一致，不匹配时返回 409。

**前端验证：** `handleDecision()` 使用 `household_id: hh!.id`，已通过校验。

### 4.2 消费审批恢复接口返回的 SSE

**状态：🔴 已修复**

**后端验证：** `app/api/routes/agent.py:217-225` 中 `decide_agent_operation` 返回 `StreamingResponse(resume_agent(...))`。`resumer.py` 通过 `StreamTracker` 发送以下 SSE 事件：`tool_started`、`tool_completed`/`tool_failed`、`message_delta`、`execution_status`、`run_completed`、`error`。

`app/agents/events/stream_tracker.py` 负责全部事件发送，`emit_execution_status` 和 `emit_execution_result` 方法已实现。

### 4.3 将审批卡从场景专用改为通用写操作审批

**状态：🔴 已修复**

**后端验证：** `app/agents/risk/classifier.py:39-219` 中 `classify_automation_operation` 返回 4 种 `kind` 的 preview：`create_automation`、`update_automation`、`set_automation_enabled`、`delete_automation`。`classify_scene_execution`（`app/agents/risk/classifier.py:222-298`）返回 `scene_execution`。

总共 5 种写操作 `kind`，对应 `app/agents/tools/__init__.py:10-16` 定义的 5 个 `WRITE_TOOL_SCHEMAS`。

### 4.4 统一自动批准与人工批准的工具事件

**状态：🔴 已修复**

**后端验证：** `app/agents/events/stream_tracker.py` 中 `emit_execution_status` 发送 `submitted`/`running`/`verified`/`failed`/`unknown` 状态。`emit_execution_result` 解析写工具节点返回的 `ToolMessage` 内容并发送最终状态。

- 首次运行（`runner.py`）：模型发出写工具调用时发送 `submitted`；写工具节点返回结果时发送 `verified`/`submitted`/`failed`。
- 恢复执行（`resumer.py`）：批准决定为 `approve` 时发送 `running`；写工具节点返回结果时发送 `verified`/`submitted`/`failed`。

两条路径均已发送 `execution_status` 事件。

---

## 5. P1：完成前端已经暴露但没有行为的功能

### 5.1 实现真正的"普通对话"模式

**状态：🔴 已修复**

**后端验证：** `app/api/routes/chat.py` 中 `/api/chat/completions` 端点存在。`app/services/chat.py` 中 `create_chat_service`/`create_chat_service_stream` 的 `_to_langchain_messages` 方法回放完整 `payload.messages` 历史给模型，实现跨轮记忆。

`ChatSession` 模型（`app/models/chat.py`）包含 `mode` 字段（`agent`/`chat`），`PATCH /chat/sessions/{id}/mode` 更新接口存在。`app/api/routes/agent.py:84-151` 中 `/agent/runs` 端点接收 `tools_enabled` 参数，对话模式不传此参数或传 `false` 时 `app/agents/prompts.py:49-59` 生成无工具 system prompt。

### 5.2 实现或移除语音输入入口

**状态：❌ 未完成**

**后端验证：** 后端无任何音频上传、语音识别（ASR）或语音合成（TTS）相关 API。`smarthome-api/app/` 下 grep 无 `audio`、`speech`、`voice`、`asr`、`tts`、`录音`、`语音` 相关路由或服务。

### 5.3 实现可靠的重新生成

**状态：🔴 已修复**

**后端验证：**

- `app/api/routes/agent.py:311-382`：`POST /sessions/{session_id}/regenerate` — 接收 `RegenerateRequest`（`target_message_id`、`model`、`household_id`），检查待确认操作（有则 409），调用 `prepare_regenerate`（`app/services/chat.py`）定位目标助手消息并删除后续消息，从 checkpoint 提取目标用户消息之前的完整历史（含 `ToolMessage`），回退 checkpoint，以"历史 + 旧用户消息"重新运行 graph。
- `app/api/routes/agent.py:72-81`：`_extract_history_before_user` 从 graph state 消息列表截取到目标用户消息为止的完整历史（含工具中间状态）。
- `app/api/routes/agent.py:364`：`await saver.adelete_thread(agent_thread_id(ctx))` 删除旧 checkpoint。
- `app/api/routes/agent.py:379`：`persist_user_message=False` 不重复保存用户消息。
- 对话模式 regenerate 接口在 `app/services/chat.py` 中实现，复用旧用户消息重新调用 `/api/chat/completions`。

### 5.4 完善停止生成与中断恢复

**状态：🔴 已修复**

**后端验证：**

- `app/api/routes/agent.py:385-397`：`GET /sessions/{session_id}/run-status` — 查询会话最近一次 run 的状态与阶段，返回 `{"status": ..., "phase": ...}`。
- `app/agents/agent_service/` 中 `runner.py`/`resumer.py` 捕获 `asyncio.CancelledError` 并记录 `cancelled`/`disconnected` 状态。
- `agent_usage` 表包含 `session_id`、`phase`（`thinking`/`executing`/`submitted`）、`status`（`completed`/`cancelled`/`failed`/`pending_confirmation`）字段。

### 5.5 处理新会话创建失败

**状态：🔴 已修复**

**后端验证：** `app/api/routes/chat.py` 中 `POST /chat/sessions` 创建会话端点存在。`app/agents/context.py:44-53` 校验 `ChatSession` 存在且属于当前用户和家庭，不存在时返回 404。

---

## 6. P1：补齐推荐提示词承诺的 Agent 能力

### 6.1 全屋状态巡检

**状态：⚠️ 部分完成**

**后端验证：** 后端有以下查询工具（`app/agents/tools/__init__.py:20-205`）：

- `list_devices`（`app/agents/tools/query/devices.py`）— 可按房间、类型、状态筛选
- `get_device`（同上）— 获取单个设备详情
- `list_device_logs`（`app/agents/tools/query/executions.py`）— 设备日志查询

**缺口：** 后端无 `inspect_household_health` 聚合工具，无法一次性返回「离线设备 + 告警 + 固件 + 长时间未上报 + 自动化失败 + 场景失败」的结构化巡检结果。Agent 只能通过多次独立查询然后依赖模型自己总结，结果不稳定。

### 6.2 今日节能建议

**状态：❌ 未完成数据闭环**

**后端验证：** `smarthome-api/app/models/` 下所有 ORM 模型（grep 确认）不存在 `energy`、`consumption`、`Electricity`、`power_usage` 等字段或表。`app/agents/tools/` 下无任何能耗查询工具。

`app/agents/subagents/router.py:10` 中 `DOMAIN_KEYWORDS` 包含 `energy` 域的关键词（"能耗"、"用电"、"费电"、"电量"、"节能"、"电费"、"功率"、"账单"），但 `DELEGATABLE_READ_ONLY_DOMAINS`（`app/agents/subagents/router.py:20`）中 `energy` 不在其中，即即使意图路由命中 `energy`，也不会委托给子 Agent 执行。

前端 `home.ts` 中 `energyToday` 固定为 `18.62`，无后端数据源。

### 6.3 晚间回家联动

**状态：⚠️ 部分完成**

**后端验证：**

- `app/agents/tools/execute/automations.py` 可创建自动化规则（含触发器、条件、动作）
- `app/agents/tools/preview/automations.py` 中 `detect_automation_conflicts` 可检测时间重叠、设备冲突和循环触发风险
- `app/agents/prompts.py:62` 中 system prompt 包含家庭时区信息（`household.timezone`）

**缺口：** Agent 没有当前时间查询工具，"今晚"的时间语义完全依赖模型自己理解。无"一次性定时"与"长期自动化"的明确区分机制。安防设备操作（门锁、摄像头）自动判为高风险，但无专门的风险策略差异。

### 6.4 设备直接控制

**状态：❌ 未完成**

**后端验证：** `app/agents/tools/__init__.py:10-16` 中 `WRITE_TOOL_NAMES` 仅包含：

```python
WRITE_TOOL_SCHEMAS = {
    "execute_scene": execute_scenes.ExecuteSceneInput,
    "create_automation": execute_automations.CreateAutomationInput,
    "update_automation": execute_automations.UpdateAutomationInput,
    "set_automation_enabled": execute_automations.SetAutomationEnabledInput,
    "delete_automation": execute_automations.DeleteAutomationInput,
}
```

后端**不存在**以下设备控制写工具：

- `switch_light`（灯光开关、亮度、色温）
- `set_temperature`（空调模式、目标温度、风速）
- `set_curtain`（窗帘开合比例）
- `set_socket`（普通插座开关）
- `lock_door`/`unlock_door`（门锁操作）
- `set_camera`/`set_alarm`（安防设备操作）

Agent 只能查询设备状态（通过 `list_devices`/`get_device`），无法直接控制。

`app/agents/tools/query/devices.py` 中 `list_devices` 返回设备列表（含名称、类型、状态、房间名等），`get_device` 返回单个设备详情（含状态、连接方式、固件、最后在线时间）。

### 6.5 日程和安全上下文工具

**状态：❌ 未完成**

**后端验证：** `smarthome-api/app/models/` 下无 `schedule`、`security_alert`、`alarm_event` 等 ORM 模型（grep 确认）。`app/agents/tools/` 下无日程查询、安全事件查询、布防/撤防等写工具。

`app/agents/subagents/router.py:12` 中 `DOMAIN_KEYWORDS` 包含 `security` 域关键词（"门锁"、"摄像头"、"安防"、"警报"、"监控"、"布防"、"撤防"、"入侵"、"锁"、"门铃"、"报警"），且 `DELEGATABLE_READ_ONLY_DOMAINS`（`app/agents/subagents/router.py:20`）包含 `security`。但该子 Agent 目前只有通用的设备查询工具，无专门的安防事件查询或处理工具。

---

## 7. P1：让智能助手设置真正生效

### 7.1 回复语言

**状态：🔴 已修复**

**后端验证：** `app/agents/context.py:75` 中 `language_value = ai.get("language", "zh-CN")` 从用户偏好解析 `language`。`app/agents/prompts.py:20-28` 中 `_resolve_language` 处理 `auto` 模式（根据当前消息是否含中文字符决定），`_language_instruction` 生成"请使用中文/英文回答"指令。`system_prompt`（`app/agents/prompts.py:39-98`）在回复要求部分包含 `language_instruction`。

`AIAssistantPreferences` 独立存储 `language` 字段，不再依赖模型 `description`。

### 7.2 回复详细程度

**状态：🔴 已修复**

**后端验证：** `app/agents/context.py:76` 中 `detail_value = ai.get("detailLevel", ai.get("detail_level", 70))` 从用户偏好解析 `detail_level`。`app/agents/prompts.py:31-36` 中 `_detail_instruction` 把 0-100 的滑块值映射为三档回答策略：

- 0-33：简洁，直接给出结论
- 34-66：适度，给出结论并简要说明原因
- 67-100：详细，给出结论、原因、步骤和相关背景

`system_prompt`（`app/agents/prompts.py:39-98`）在回复要求部分包含 `detail_instruction`。

### 7.3 高风险二次确认

**状态：❌ 未完成**

**后端验证：** `app/agents/context.py:72-73` 确实从用户偏好解析了 `confirmHighRisk`：

```python
confirm_value = ai.get(
    "confirmHighRisk", ai.get("confirm_high_risk", True)
)
```

`AgentContext`（`app/agents/context.py:20`）包含 `confirm_high_risk: bool` 字段。

但风险分类器**从未读取该字段**：

`app/agents/risk/classifier.py:261-264` 中场景执行的风险判定：

```python
requires_approval = (
    level in {RiskLevel.HIGH, RiskLevel.UNKNOWN}
    or not context.auto_execute_low_risk
)
```

注释明确说明："高风险 / 未知风险始终需要审批，不受 confirm_high_risk 配置影响（§5.1）：安全策略不允许绕过高风险审批，confirm_high_risk 仅用于前端 UI 展示。"

自动化操作（`app/agents/risk/classifier.py:213-219`）：`classify_automation_operation` 固定返回 `requires_approval=True`，完全不受任何偏好设置影响。

因此无论 `confirm_high_risk` 如何设置，高风险操作始终要求确认——相当于"始终确认"在分类器层被强制。

### 7.4 模型选择的作用域

**状态：🔴 已修复**

**后端验证：** `app/api/routes/agent.py:207-215` 中审批恢复时固定使用原模型：

```python
model_id = pending.get("model_id")
model_name = pending.get("model_name") or None
model_config = _get_agent_model(
    db, current_user.id,
    model_name=model_name,
    model_id=int(model_id) if isinstance(model_id, int) else None,
)
```

`app/agents/graph/state.py:14` 中 `AgentState` 包含 `model_name` 字段，`risk_node.py:61-62` 将其保存到 `pending`。`ChatSession` 模型包含 `model_name` 字段，`PATCH /chat/sessions/{id}/model` 更新接口存在。

---

## 8. P2：上下文侧栏与执行结果联动

### 8.1 返回结构化受影响资源

**状态：⚠️ 部分完成**

**后端验证：** `app/agents/tools/execute/automations.py` 中写工具执行结果包含 `automation_id`、`automation_name`、`version` 等结构化字段，但无 `resource_type`/`resource_id` 通用字段。`app/agents/events/stream_tracker.py` 的 SSE 事件中 `ToolCompletedEvent` 的 `result` 是字符串，未拆分为 `resource_type`/`resource_id` 等结构化字段。

### 8.2 执行后刷新真实业务数据

**状态：⚠️ 部分完成**

**后端验证：** 后端在写工具执行后返回 `ok`/`status`/`automation_id`/`version` 等结果（`app/agents/tools/execute/automations.py`），但无统一的事件通知前端刷新特定 store 的机制。

### 8.3 用真实数据替换本地概览

**状态：❌ 未完成**

**后端验证：** `home.ts` 中 `energyToday` 固定值（`18.62`）。后端无能耗数据模型（`smarthome-api/app/models/` 下无能耗相关表）。`automations` 在 `home.ts` store 中未实际加载。安全告警处理为本地布尔值。

---

## 9. 前后端契约和测试

### 9.1 统一 OpenAPI 和 TypeScript 类型

**状态：⚠️ 部分完成**

**后端验证：** `app/schemas/agent.py` 定义了 `AgentRunRequest`、`AgentDecisionRequest`、`PendingApprovalRead` 等 Pydantic 模型。`app/schemas/sse.py` 定义了 SSE 事件模型。前端 `types/chat.ts` 手写了对应的 TypeScript 接口。

缺乏自动生成 TypeScript 类型的机制，前端手写类型已有偏差（如 `PendingApproval.preview` 类型为 `Record<string, unknown>` 而非精确的判别联合类型）。

### 9.2 必须增加的端到端测试

**状态：❌ 未完成**

**后端验证：** `smarthome-api/tests/` 下无 Agent 相关端到端测试。`test_subagents.py` 和 `test_scene_execute.py` 存在但仅覆盖单元级别。

---

## 10. 后端能力矩阵总览

以下矩阵汇总了后端所有 Agent 相关工具与数据模型，方便与前端能力对照：

### 查询工具（只读，11 个）

| 工具名 | 后端文件 | 功能 |
| --- | --- | --- |
| `list_rooms` | `app/agents/tools/query/rooms.py` | 列出房间 |
| `get_room` | 同上 | 获取房间详情 |
| `list_devices` | `app/agents/tools/query/devices.py` | 列出设备 |
| `get_device` | 同上 | 获取设备详情 |
| `list_scenes` | `app/agents/tools/query/scenes.py` | 列出场景 |
| `get_scene` | 同上 | 获取场景详情 |
| `list_automations` | `app/agents/tools/query/automations.py` | 列出自动化规则 |
| `get_automation` | 同上 | 获取自动化规则详情 |
| `list_device_logs` | `app/agents/tools/query/executions.py` | 查询设备日志 |
| `list_scene_executions` | 同上 | 查询场景执行记录 |
| `list_automation_executions` | 同上 | 查询自动化执行记录 |

### 预览工具（只读，3 个）

| 工具名 | 后端文件 | 功能 |
| --- | --- | --- |
| `preview_scene` | `app/agents/tools/preview/scenes.py` | 预览场景执行步骤 |
| `preview_automation_change` | `app/agents/tools/preview/automations.py` | 预览自动化变更差异 |
| `detect_automation_conflicts` | 同上 | 检测自动化规则冲突 |

### 写工具（需审批，5 个）

| 工具名 | 后端文件 | 风险策略 |
| --- | --- | --- |
| `execute_scene` | `app/agents/tools/execute/scenes.py` | `classify_scene_execution` 返回 LOW/HIGH/UNKNOWN |
| `create_automation` | `app/agents/tools/execute/automations.py` | `classify_automation_operation` 固定 `requires_approval=True` |
| `update_automation` | 同上 | 同上 |
| `set_automation_enabled` | 同上 | 同上 |
| `delete_automation` | 同上 | 同上 |

### 子 Agent 领域（已注册但部分未就绪）

| 领域 | 可委托？ | 工具就绪？ |
| --- | --- | --- |
| `device` | ✅ 只读可委托 | ✅ 有查询工具 |
| `scene` | ✅ 写能力域 | ✅ 有查询 + 写工具 |
| `automation` | ✅ 写能力域 | ✅ 有查询 + 预览 + 写工具 |
| `energy` | ❌ 尚未可委托 | ❌ 无能耗数据模型 |
| `comfort` | ❌ 尚未可委托 | ❌ 无温湿度等舒适度数据 |
| `security` | ✅ 只读可委托 | ⚠️ 仅有通用设备查询，无安防专用工具 |
| `general` | 兜底 | 不适用 |

### 后端 API 端点汇总

| 端点 | 方法 | 后端文件 | 功能 |
| --- | --- | --- | --- |
| `/api/agent/runs` | POST | `app/api/routes/agent.py:84-151` | 创建 Agent 运行 |
| `/api/agent/sessions/{id}/decisions` | POST | `app/api/routes/agent.py:154-225` | 审批决定 |
| `/api/agent/sessions/{id}/pending` | GET | `app/api/routes/agent.py:228-264` | 查询待审批操作 |
| `/api/agent/sessions/{id}/cancel-pending` | POST | `app/api/routes/agent.py:267-308` | 取消待审批 |
| `/api/agent/sessions/{id}/regenerate` | POST | `app/api/routes/agent.py:311-382` | 重新生成 |
| `/api/agent/sessions/{id}/run-status` | GET | `app/api/routes/agent.py:385-397` | 查询运行状态 |
| `/api/chat/completions` | POST | `app/api/routes/chat.py` | 对话模式（无工具） |
| `/api/chat/sessions/{id}/regenerate` | POST | `app/services/chat.py` | 对话模式重新生成 |
| `PATCH /chat/sessions/{id}/mode` | PATCH | `app/api/routes/chat.py` | 更新会话模式 |
| `PATCH /chat/sessions/{id}/model` | PATCH | `app/api/routes/chat.py` | 更新会话模型 |

---

## 11. 推荐实施顺序

**当前 P0 审批链状态：✅ 全部完成**

建议按以下顺序推进剩余工作：

1. **删除或修正 `confirm_high_risk` 设置项**：后端已解析但分类器强制高风险审批，要么删除该开关避免误导用户，要么修正其语义（`app/agents/risk/classifier.py:261-264` 注释明确说明安全策略不允许绕过高风险审批——建议删除前端设置项）。

2. **接入推荐提示词对应的真实工具**（可基于已落地的子 Agent 框架 `app/agents/subagents/` 实现）：
   - 能耗数据模型与查询工具（`energy` 域）
   - 设备控制写工具（`switch_light`、`set_temperature` 等）
   - 全屋巡检聚合工具（`inspect_household_health`）
   - 安防事件模型与工具（`security` 域）

3. **用结构化资源 ID 驱动右侧上下文卡**：在工具结果和 SSE 事件中增加 `resource_type`/`resource_id` 通用字段。

4. **补端到端测试**覆盖审批链（批准、拒绝、版本冲突、模型切换、刷新恢复）。

5. **语音输入**：后端先增加音频上传和 ASR 转写 API，前端再实现录音与权限流程。

---

## 12. 后端验证清单

以下为本次验证中实际检查的后端代码文件：

- `smarthome-api/app/agents/context.py` — AgentContext 字段与解析逻辑
- `smarthome-api/app/agents/prompts.py` — system prompt 生成（语言、详细程度、安全约束）
- `smarthome-api/app/agents/graph/` — 状态机（`state.py`、`tool_router.py`、`risk_node.py`、`approval.py`、`execute.py`、`nodes.py`、`__init__.py`）
- `smarthome-api/app/agents/tools/__init__.py` — 工具注册表（WRITE_TOOL_NAMES、WRITE_TOOL_SCHEMAS、get_household_tools）
- `smarthome-api/app/agents/tools/query/` — 查询工具（devices、rooms、scenes、automations、executions）
- `smarthome-api/app/agents/tools/execute/` — 写工具（scenes、automations）
- `smarthome-api/app/agents/tools/preview/` — 预览工具（scenes、automations）
- `smarthome-api/app/agents/risk/classifier.py` — 风险分类器（confirm_high_risk/auto_execute_low_risk 使用情况）
- `smarthome-api/app/agents/events/stream_tracker.py` — SSE 事件发送
- `smarthome-api/app/agents/agent_service/runner.py` — 首次运行
- `smarthome-api/app/agents/agent_service/resumer.py` — 恢复执行
- `smarthome-api/app/agents/subagents/` — 子 Agent（router.py、factory.py、contracts.py）
- `smarthome-api/app/api/routes/agent.py` — Agent REST API
- `smarthome-api/app/api/routes/chat.py` — 对话 REST API
- `smarthome-api/app/schemas/agent.py` — Agent 请求/响应 schema
- `smarthome-api/app/models/` — 所有 ORM 模型
- `smarthome-api/app/services/chat.py` — 聊天服务（跨轮记忆、regenerate）
- `smarthome-api/app/services/session_tree.py` — 会话树接入层
- `smarthome-api/app/compaction/` — 上下文压缩
- `smarthome-api/app/session_tree/` — 会话树存储
