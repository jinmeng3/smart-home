# LangChain 智能家居智能体设计方案

> 本文档描述在现有 smart-home 项目中接入 LangChain 智能体的目标架构、接口协议、安全策略和实施步骤。
>
> 本文档只保留设计决策与接口协议；实施方向与开发指导见 [11-langchain-agent-guidance.md](./11-langchain-agent-guidance.md)，现状审查与进展盘点见 [12-agent-review-and-roadmap.md](./12-agent-review-and-roadmap.md)。
>
> **当前状态**：📝 目标设计稿。`smarthome-api/app/agents/` 已包含上下文、提示词、模型工厂、异常与 checkpointer 等基础设施雏形，但工具注册、运行图、人工确认与 SSE 协议尚未实现；实现进度对照见 12 号文档。

---

## 1. 背景与目标

当前聊天模块已经具备以下能力：

- 管理用户级 AI 模型配置；
- 保存聊天会话和消息；
- 将请求转发到 OpenAI 兼容的 `/chat/completions` 接口；
- 通过 SSE 向前端流式返回文本。

当前后端只负责模型请求转发，模型不能查询家庭数据或调用业务服务。前端展示的“理解指令、请求模型、生成回复、整理结果”也是固定进度，并非真实工具执行状态。

本次改造目标是将聊天模块升级为可查询和操作智能家居业务的 LangChain 智能体：

1. 原生支持 OpenAI、Anthropic 和 Google Gemini；
2. 查询房间、设备、场景和自动化数据；
3. 执行现有场景和自动化；
4. 创建、修改、启停和删除自动化规则；
5. 对写操作执行风险分级和人工确认；
6. 将模型输出、工具执行和待确认状态实时展示给前端；
7. 保证用户只能访问当前选择且有成员权限的家庭。

### 1.1 本期不包含

- 不接入真实 Home Assistant、MQTT、Matter 或 Zigbee 控制通道；
- 不实现新的自动化调度器；
- 不重构现有场景和自动化执行引擎；
- 不开放任意 Python、SQL、HTTP 请求或文件操作工具；
- 不支持智能体自行选择用户的家庭。

> 当前 `run_scene_service` 主要生成成功日志，`execute_automation_service` 主要创建 `running` 执行记录。因此智能体只能准确描述为“已提交”或“已记录”，不能声称物理设备已经执行成功。

---

## 2. 总体架构

```text
Vue Chat UI
    │
    │  POST /api/chat/completions
    │  household_id + session_id + message
    ▼
FastAPI Chat Route
    │
    ├── 身份认证与家庭成员校验
    ├── AI 模型工厂
    └── LangChain Agent
           │
           ├── 只读工具 ──► Room / Device / Scene / Automation Service
           ├── 执行工具 ──► Scene / Automation Service
           ├── 管理工具 ──► Automation Service
           ├── 风险策略与人工确认
           └── LangGraph Checkpointer
                    │
                    └── SQLite（当前开发环境）
```

改造遵循现有后端的分层方式：

- Route 负责认证、请求校验和响应协议；
- Agent Service 负责创建、运行和恢复智能体；
- Tool 只负责将结构化参数适配到现有业务 Service；
- 业务校验、家庭归属和数据库事务继续由现有 Service 负责；
- Schema 使用 Pydantic，并保持现有 snake_case 输入和别名策略。

---

## 3. 模型接入

### 3.1 支持范围

| provider | LangChain 适配器 | endpoint 规则 |
|----------|------------------|---------------|
| `openai` | `langchain-openai` | 可使用官方地址或自定义兼容地址 |
| `anthropic` | `langchain-anthropic` | endpoint 可选，默认使用官方地址 |
| `google` | `langchain-google-genai` | endpoint 可选，默认使用官方地址 |

模型工厂从当前用户启用的 `ai_models` 记录读取：

- `provider`；
- `name`；
- `api_key`；
- `api_endpoint`；
- `temperature`；
- `max_tokens`；
- `parameters`。

`provider` 必须是 `openai`、`anthropic` 或 `google`。未知提供商直接返回可读错误，不静默回退到其他模型。

### 3.2 配置调整

现有 `api_endpoint` 是必填字段。接入原生提供商后应调整为可选：

```json
{
  "name": "claude-sonnet",
  "provider": "anthropic",
  "apiEndpoint": null,
  "apiKey": "***",
  "temperature": 0.3,
  "maxTokens": 4096,
  "isActive": true
}
```

模型必须支持工具调用。若模型只支持文本补全，应在智能体启动前返回明确错误，不降级为可能误导用户的“伪工具调用”。

---

## 4. Agent 上下文与记忆

每次运行向 Agent 注入可信运行上下文：

```python
class AgentContext:
    user_id: int
    household_id: int
    session_id: int
    auto_execute_low_risk: bool
    confirm_high_risk: bool
```

这些字段由后端根据登录用户、请求和用户设置构造，不能由模型通过工具参数覆盖。

系统提示至少包含以下规则：

1. 默认使用用户配置的语言回复；
2. 查询或操作前优先确认实体是否存在；
3. 不猜测设备、场景和自动化 ID；
4. 不得访问当前 `household_id` 之外的数据；
5. 工具失败时解释原因，不伪造成功结果；
6. 执行结果必须区分“请求已提交”和“设备已实际响应”；
7. 缺少必要参数时先追问，不自行补造高影响参数。

使用 LangGraph SQLite checkpointer 保存 Agent 的消息状态、工具调用结果和人工确认中断。现有数据的职责保持如下：

| 数据 | 存储位置 | 用途 |
|------|----------|------|
| 用户可见消息 | `chat_messages` | 历史会话展示 |
| 会话标题与归属 | `chat_sessions` | 会话列表和权限校验 |
| 工具消息与运行状态 | LangGraph checkpoint | 多步执行和中断恢复 |
| 业务执行记录 | 现有场景/自动化日志表 | 业务审计 |

`chat_session.id` 作为 LangGraph `thread_id`。用户刷新页面后，仍可恢复尚未处理的确认请求。

---

## 5. 工具设计

工具不直接操作 SQLAlchemy Model，而是调用现有 Service，复用归属校验、Pydantic 校验、乐观锁和事务逻辑。

### 5.1 查询工具

| 工具 | 功能 | 是否确认 |
|------|------|----------|
| `list_rooms` | 查询当前家庭房间 | 否 |
| `list_devices` | 按房间、类型或状态查询设备 | 否 |
| `get_device` | 查询设备详情 | 否 |
| `list_scenes` | 查询可用场景 | 否 |
| `preview_scene` | 预览场景步骤和风险 | 否 |
| `list_automations` | 查询自动化规则 | 否 |
| `get_automation` | 查询自动化完整配置 | 否 |
| `list_automation_executions` | 查询执行记录 | 否 |

### 5.2 执行工具

| 工具 | 功能 | 确认策略 |
|------|------|----------|
| `execute_scene` | 执行已有场景 | 低风险可自动执行，高风险必须确认 |
| `execute_automation` | 手动触发已有自动化 | 低风险可自动执行，高风险必须确认 |

`execute_automation` 为每次 Agent 工具调用生成幂等键。网络重试、SSE 重连或用户重复点击不能产生重复执行记录。

### 5.3 自动化管理工具

| 工具 | 功能 | 允许的人工决策 |
|------|------|----------------|
| `create_automation` | 创建自动化规则 | approve / edit / reject |
| `update_automation` | 修改自动化规则 | approve / edit / reject |
| `set_automation_enabled` | 启用或停用规则 | approve / reject |
| `delete_automation` | 删除规则 | approve / reject |

创建和更新工具直接复用 `AutomationCreate`、`AutomationUpdate` Schema。更新时必须传递当前 `version`，若发生 `409` 版本冲突，Agent 应重新读取规则并向用户说明冲突，不能自动覆盖。

---

## 6. 风险与确认策略

风险判定必须在后端执行，不能只依赖模型判断或当前前端的关键词逻辑。

### 6.1 风险等级

| 等级 | 示例 | 行为 |
|------|------|------|
| 只读 | 查询温度、设备、场景、执行记录 | 直接执行 |
| 低风险执行 | 普通灯光、空调等非安防场景或自动化 | 用户开启“低风险操作自动执行”时直接执行 |
| 高风险执行 | 门锁、摄像头、安防设备，或 `high_risk=true` 的场景 | 必须确认 |
| 配置变更 | 创建、修改、启停、删除自动化 | 必须确认 |
| 未知风险 | 无法解析的设备或动作类型 | 按高风险处理 |

### 6.2 确认流程

```text
模型生成工具调用
    │
    ├── 只读或允许自动执行的低风险动作 ──► 执行工具
    │
    └── 需要确认
           │
           ├── 保存 interrupt
           ├── SSE 推送 approval_required
           └── 等待用户 approve / edit / reject
```

确认卡片展示：

- 操作名称和风险等级；
- 当前家庭；
- 目标场景、自动化或设备；
- 影响设备和关键参数；
- 需要确认的原因；
- 可用决策按钮。

拒绝操作后，后端向 Agent 注入拒绝结果，由 Agent 给出简短说明，不能执行原工具。

---

## 7. API 协议

### 7.1 运行智能体

- **方法**：`POST /api/chat/completions`
- **认证**：需要登录
- **功能**：在指定家庭上下文中运行智能体

请求：

```json
{
  "session_id": 12,
  "household_id": 3,
  "messages": [
    {
      "role": "user",
      "content": "每天晚上十点关闭客厅灯"
    }
  ],
  "stream": true
}
```

校验规则：

- `household_id` 必填且必须为正整数；
- 当前用户必须是该家庭成员；
- `session_id` 必须属于当前用户；
- 智能体模式仅支持 `stream=true`；
- 同一会话存在未处理确认时，不允许启动新的写操作运行。

### 7.2 处理确认请求

- **方法**：`POST /api/chat/sessions/{session_id}/decisions`
- **认证**：需要登录
- **功能**：恢复被人工确认中断的 Agent

批准：

```json
{
  "interrupt_id": "interrupt-123",
  "decision": "approve"
}
```

编辑后批准：

```json
{
  "interrupt_id": "interrupt-123",
  "decision": "edit",
  "edited_arguments": {
    "name": "夜间关闭客厅灯",
    "enabled": false,
    "triggers": [],
    "conditions": [],
    "actions": []
  }
}
```

拒绝：

```json
{
  "interrupt_id": "interrupt-123",
  "decision": "reject",
  "reason": "先不要创建"
}
```

后端必须校验 interrupt 所属用户、会话和家庭。已处理、过期或不匹配的 interrupt 返回 `409` 或 `404`，不得重复执行。

### 7.3 SSE 事件

所有事件使用统一结构：

```text
event: message_delta
data: {"content":"正在为你整理自动化方案"}
```

| event | data 关键字段 | 说明 |
|-------|---------------|------|
| `message_delta` | `content` | 助手文本增量 |
| `tool_started` | `callId`, `tool`, `summary` | 工具开始执行 |
| `tool_completed` | `callId`, `tool`, `result` | 工具执行成功 |
| `tool_failed` | `callId`, `tool`, `error` | 工具执行失败 |
| `approval_required` | `interruptId`, `action`, `risk`, `arguments`, `allowedDecisions` | 等待用户确认 |
| `agent_completed` | `sessionId`, `status` | 本轮结束 |
| `error` | `code`, `message`, `retryable` | 运行错误 |

`POST /api/v1/chat/completions` 暂时保留为普通 OpenAI 兼容文本补全接口，不绑定智能家居工具，防止第三方客户端绕过家庭选择和确认流程。

---

## 8. 前端改造

### 8.1 家庭上下文

聊天页必须展示并提交当前选中的家庭。用户没有选择家庭时：

- 可以开始普通问答；
- 不允许发起智能家居查询或控制；
- UI 提示用户先选择家庭；
- 不能自动选择用户加入的第一个家庭。

### 8.2 执行状态

`useHomeChat` 不再生成固定的四个步骤，而是根据 SSE 事件维护执行状态：

- `tool_started` 创建或更新执行步骤；
- `tool_completed` 标记成功；
- `tool_failed` 标记失败并显示原因；
- `approval_required` 展示确认卡片；
- `message_delta` 继续增量更新助手消息。

用户点击“停止生成”只中止当前浏览器的流读取。已经提交到后端的写操作不能显示为“已撤销”。

### 8.3 待确认恢复

加载历史会话时，同时读取该会话的待确认状态。若存在 interrupt，恢复确认卡片，不要求用户重新输入原始指令。

---

## 9. 数据与安全

1. 工具参数中不接受 `user_id`，`household_id` 只从可信上下文读取；
2. 所有实体查询都附带家庭归属条件；
3. 工具输出只返回模型完成任务所需的最少字段；
4. API Key、JWT、数据库异常和堆栈不得进入模型上下文或 SSE；
5. 删除和配置变更必须留下用户、会话、工具参数和确认结果审计信息；
6. 工具调用设置最大轮数和超时，防止无限循环；
7. 单次运行禁止并行执行多个写工具，避免事务顺序不确定；
8. 模型生成的文本不作为执行成功依据，工具返回值才是唯一事实来源。

现有 API Key 为数据库明文存储。本次可以继续沿用以控制改造范围，但生产部署前应增加加密存储或外部密钥管理。

---

## 10. 后续演进

首版稳定后，可按以下顺序扩展：

1. 接入 Home Assistant WebSocket/REST API，建立设备与实体映射；
2. 将执行结果从“已提交”升级为设备状态回读验证；
3. 使用 PostgreSQL checkpointer 支持多实例部署；
4. 增加 LangSmith 或等价链路观测，但对敏感家庭数据做脱敏；
5. 增加长期偏好记忆，并提供用户查看和删除入口；
6. 根据模型能力和任务复杂度进行动态模型路由；
7. 为自动化方案增加 dry-run、冲突检测和影响分析。
