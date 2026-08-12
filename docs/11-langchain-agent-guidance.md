# LangChain Agent 实施方向与开发指导

> 本文基于当前 `smart-home` 项目的实际结构，指导如何使用 LangChain/LangGraph 扩展智能家居能力。
>
> 当前 agent 相关代码主要位于 `smarthome-api/app/agents`，已有 `AgentContext`、system prompt、模型工厂、异常类型和 checkpointer 雏形；聊天、设备、场景、自动化等基础业务能力已经存在，但完整的 agent 运行链路和工具层尚未形成。
>
> 设计审查与风险清单见 [12-agent-review-and-roadmap.md](./12-agent-review-and-roadmap.md)，目标架构草案见 [10-langchain-agent.md](./10-langchain-agent.md)。

---

## 1. 适合当前项目的 LangChain 使用方向

### 1.1 家庭状态问答

这是最适合优先落地的方向，主要使用只读工具，不直接改变设备状态。

用户可以询问：

- “客厅有哪些设备？”
- “哪些设备当前离线？”
- “帮我检查全屋设备状态。”
- “最近有哪些场景执行失败？”
- “卧室温度和空调状态怎么样？”

可接入的工具：

- `list_rooms`
- `list_devices`
- `get_device`
- `list_scenes`
- `get_scene`
- `list_automations`
- `list_execution_logs`

实现重点：

- 工具只读取当前家庭数据；
- 返回给模型的字段尽量精简；
- 将数据库状态和推断性建议分开；
- 没有查询到数据时明确返回空结果，不让模型自行猜测。

### 1.2 家庭运维巡检

基于当前设备、设备日志、场景执行日志和自动化执行记录，可以实现一个运维助手：

1. 查询家庭内设备和执行记录；
2. 找出离线设备、长期未响应设备和近期失败操作；
3. 按严重程度归类问题；
4. 给出排查建议；
5. 需要用户操作时只生成建议，不直接执行高风险动作。

建议将结果设计成结构化对象：

```json
{
  "summary": "发现 2 个需要关注的问题",
  "issues": [
    {
      "severity": "warning",
      "category": "device_offline",
      "target": "客厅空气净化器",
      "evidence": "最近在线时间超过 24 小时",
      "suggestions": ["检查电源", "检查网络连接"]
    }
  ]
}
```

LangChain 负责理解问题、组织查询和生成解释；问题判定的事实应来自工具结果。

### 1.3 场景推荐与预览

当前项目已有 Scene、SceneStep、SceneTemplate、SceneExecutionLog 等模型，可以让 agent 根据用户意图推荐或预览场景：

- 根据“回家”“睡眠”“节能”等意图推荐现有场景；
- 展示场景包含哪些设备和步骤；
- 判断是否包含门锁、摄像头、安防等高风险设备；
- 提示场景是否启用、最近是否执行成功；
- 在执行前生成影响范围预览。

第一阶段只做 `preview_scene`，不执行。这样可以验证自然语言解析、工具调用和风险展示，而不会引入控制风险。

### 1.4 低风险场景执行

在只读 agent 稳定后，可以增加场景执行能力，例如执行普通灯光、空调或非安防设备场景。

推荐流程：

```text
用户请求
  -> 查询场景
  -> 预览场景动作
  -> 后端风险评估
  -> 低风险且允许自动执行？
       -> 是：执行
       -> 否：创建确认请求
  -> 返回业务执行状态
```

不要让模型自行决定“是否安全”。模型只负责提出工具调用，风险分类和是否需要确认由后端完成。

### 1.5 自动化草案生成

当前项目已有自动化模型、Schema、CRUD Service 和前端创建/编辑能力，适合先实现“生成草案”，而不是直接创建自动化。

例如：

> 每天晚上十点关闭客厅灯，周末不要执行。

Agent 应生成结构化草案：

```json
{
  "name": "工作日夜间关闭客厅灯",
  "triggers": [
    { "type": "schedule", "time": "22:00", "days": ["mon", "tue", "wed", "thu", "fri"] }
  ],
  "conditions": [],
  "actions": [
    { "device_id": "...", "action": "turn_off" }
  ]
}
```

然后交给前端展示 diff 和编辑表单。只有用户确认后，后端才调用现有自动化 Service 写入数据库。

### 1.6 自动化解释与冲突分析

在自动化管理之前，可以先实现低风险的分析能力：

- 解释某条自动化的触发条件和动作；
- 检查时间重叠；
- 检查同一设备在同一时间的冲突动作；
- 识别可能导致循环触发的规则；
- 对比修改前后的配置差异；
- 解释某条自动化最近没有执行的原因。

这些能力可以复用现有 Automation Service，并通过结构化工具结果实现，比直接让模型自由生成 SQL 或业务对象更可靠。

### 1.7 节能建议

当前设备、房间、场景和执行记录可以支持基础节能分析：

- 识别长时间运行的设备；
- 识别频繁启停的设备；
- 统计场景执行频率；
- 发现可能重复的自动化；
- 给出“建议关闭”“建议调整时间”等解释性建议。

如果项目后续接入真实能耗数据，再增加按日、周、月的能耗分析。当前不要把设备运行次数直接描述成精确能耗。

### 1.8 多轮家庭助手

`ChatSession` 和 `ChatMessage` 可以作为用户可见会话历史，LangGraph checkpoint 适合保存当前运行中的工具调用和确认状态。

需要区分两类数据：

| 数据 | 推荐用途 |
|---|---|
| `chat_sessions` / `chat_messages` | 用户可见的聊天历史 |
| LangGraph checkpoint | 当前 agent 运行状态、工具消息和中断恢复 |
| 业务日志表 | 场景、自动化和设备的事实记录 |
| Agent audit log | 工具调用、参数、风险判断和确认决策 |

不要只把完整 checkpoint 当作永久聊天历史，也不要只依靠聊天文本恢复待确认写操作。

---

## 2. 推荐技术架构

### 2.1 分层方式

建议保持现有 FastAPI 分层，并增加以下 agent 层：

```text
Vue Chat UI
    │
    ├── 普通聊天 API
    └── Agent Run API / Decision API
             │
             ▼
        Agent Service
             │
             ├── AgentContext
             ├── Model Factory
             ├── Prompt Builder
             ├── Risk Policy
             ├── Tool Registry
             ├── Checkpointer
             └── Event Publisher
                      │
                      ▼
             Existing Business Services
             ├── Device Service
             ├── Scene Service
             ├── Automation Service
             └── Room / Overview Service
```

职责建议：

- **Route**：认证、请求校验、SSE 响应和确认请求入口；
- **Agent Service**：创建 graph、注入上下文、运行和恢复；
- **Model Factory**：根据模型配置创建对应 ChatModel；
- **Tool**：接收严格结构化参数，调用现有 Service；
- **Risk Policy**：判断工具和具体动作的风险；
- **Event Publisher**：将模型、工具、确认和错误状态转换为前端事件；
- **Existing Service**：负责业务规则、家庭归属和数据库事务。

### 2.2 LangChain 与 LangGraph 的分工

建议使用：

- **LangChain**：ChatModel、Prompt、Tool、结构化输出和模型适配；
- **LangGraph**：多步运行状态、工具循环、人工确认中断和恢复；
- **Pydantic**：工具输入、结构化输出、确认参数和 SSE 数据模型；
- **SQLAlchemy Service**：实际业务读写和事务控制。

只使用 LangChain AgentExecutor 也能完成简单工具调用，但当前项目需要人工确认、恢复、幂等和多步状态，长期更适合使用显式 LangGraph 状态图。

### 2.3 推荐目录结构

本节把前述分层、LangGraph 节点、工具分类、API 与 SSE、Provider 适配落地为具体文件布局，便于开发时按图实施。整体划分为后端 `agents` 包、agent API 路由、Schema 与现有业务接入层，以及前端聊天状态流。

#### 后端：`smarthome-api/app/`

```text
app/
├─ agents/                          # agent 核心包
│  ├─ __init__.py                   # 聚合导出：get_agent_graph、工具注册、异常
│  ├─ context.py                    # AgentContext 与可信上下文组装（已有雏形）
│  ├─ prompts.py                    # Prompt Builder：系统提示注入家庭概况与运行规则
│  ├─ errors.py                     # AgentError 与各类业务/模型/工具异常（已有雏形）
│  ├─ factory.py                    # Model Factory：模型创建 + Provider 适配 + 缓存
│  ├─ checkpointer.py               # Checkpointer：Agent 运行状态与中断恢复（已有雏形）
│  ├─ graph/                        # LangGraph 状态图
│  │  ├─ __init__.py
│  │  ├─ state.py                   # AgentState：消息、上下文、工具调用、确认等状态字段
│  │  ├─ nodes.py                   # load_context / load_history / model / finalize 节点
│  │  ├─ tool_router.py             # tool_router / read_tool 节点与工具循环边界
│  │  ├─ risk_node.py               # risk_check 节点：写操作后端风险判定
│  │  ├─ approval.py                # approval_interrupt 节点：创建并等待确认
│  │  └─ execute.py                 # write_tool 节点：执行已批准写操作
│  ├─ tools/                        # Tool 层，只做参数适配，复用现有 Service
│  │  ├─ __init__.py                # 工具注册表：按启用的阶段注册工具集合
│  │  ├─ base.py                    # 工具基类：注入上下文、归属校验、超时、脱敏、审计
│  │  ├─ query/                     # 只读查询工具
│  │  │  ├─ rooms.py                # list_rooms
│  │  │  ├─ devices.py              # list_devices / get_device
│  │  │  ├─ scenes.py               # list_scenes / get_scene
│  │  │  ├─ automations.py          # list_automations / get_automation
│  │  │  └─ executions.py           # list_execution_logs
│  │  ├─ preview/                   # 预览分析工具（只读、不执行）
│  │  │  ├─ scenes.py               # preview_scene
│  │  │  ├─ automations.py          # preview_automation_change / detect_automation_conflicts
│  │  │  └─ household.py            # 状态巡检 / 节能建议
│  │  └─ execute/                   # 写工具（进入风险与确认流程）
│  │     ├─ scenes.py               # execute_scene
│  │     ├─ automations.py          # create / update / set_enabled / delete
│  │     └─ low_risk.py             # 低风险设备动作（后期按阶段开放）
│  ├─ risk/                         # 风险策略
│  │  ├─ __init__.py
│  │  ├─ policy.py                  # 风险接口与枚举：只读/低风险/高风险/配置变更/未知
│  │  ├─ classifier.py              # 按目标设备/场景/自动化展开判定风险
│  │  └─ profile.py                 # 综合系统策略∩家庭策略∩用户偏好计算最终策略
│  ├─ agentservice/                 # Agent Service：创建图、注入上下文、运行与恢复
│  │  ├─ __init__.py
│  │  ├─ runner.py                  # run：绑定工具与模型，接受流式事件回调
│  │  ├─ resumer.py                 # resume：处理 approve / edit / reject 决策
│  │  └─ context_builder.py         # 组装 AgentContext 并持久化为审计快照
│  ├─ events/                       # Event Publisher：agent/SSE 事件模型与分发
│  │  ├─ __init__.py
│  │  ├─ models.py                  # run_*, tool_*, approval_required, error 事件结构
│  │  ├─ sse.py                     # 将 agent 事件编码为 SSE 帧（text/event-stream）
│  │  └─ publisher.py               # 事件分发给当前连接/会话订阅者
│  └─ audit/                        # Agent 审计
│     ├─ __init__.py
│     ├─ recorder.py                # 记录运行、工具调用、参数、风险判定和确认决策
│     └─ policy.py                  # 审计保留期、脱敏规则与事件 schema 版本
├─ api/
│  ├─ routes/
│  │  └─ agent.py                   # /api/agent/* 路由：认证、校验、SSE 与决策入口
├─ schemas/
│  ├─ agent.py                      # Runs 请求/响应、Decision 请求、Pending 响应
│  └─ sse.py                        # SSE 事件 Pydantic 模型（与 events/models 对应）
```

#### 后端：现有业务接入（不动现有 Service，只新增薄适配）

```text
app/services/
├─ agent_service/
│  ├─ __init__.py
│  ├─ room_agent.py                 # 复用房间查询能力
│  ├─ device_agent.py               # 复用设备列表/详情/日志
│  ├─ scene_agent.py                # 复用场景列表/详情/预览/执行
│  └─ automation_agent.py           # 复用自动化查询/预览/写入/冲突检测
```

> 这些文件只是“胶水”：把 `AgentContext` 与既有 Service、家庭归属、事务组合成工具可调用的函数，不复制业务逻辑。

#### 前端：`smarthome-web/src/`

```text
src/
├─ api/
│  ├─ agent.ts                      # agent API 请求：run、decision、pending
│  └─ agentSse.ts                   # agent SSE 解析：按事件类型分发到回调
├─ composables/
│  ├─ useAgentChat.ts               # 基于结构化 SSE 事件驱动消息与执行状态（替代固定四步）
│  └─ useAgentConfirmation.ts       # 待确认状态：拉取 pending、展示确认卡片、提交决策
├─ stores/
│  └─ agent.ts                      # Pinia：agent 状态、运行步骤、待确认队列、活跃会话
├─ types/
│  └─ agent.ts                      # AgentEvent、AgentExecutionStep、AgentStatus、Decision 类型
└─ components/
   └─ chat/
      ├─ AgentConfirmationCard.vue  # approve / edit / reject 确认卡片
      └─ AgentExecutionPanel.vue    # 真实工具执行进度面板
```

#### 目录对应关系

| 指导内容 | 落位 |
|---|---|
| AgentContext | `agents/context.py`、`agents/agentservice/context_builder.py` |
| LangGraph 图 | `agents/graph/`（state / nodes / tool_router / risk_node / approval / execute） |
| Model Factory + Provider | `agents/factory.py` |
| Prompt Builder | `agents/prompts.py` |
| Checkpointer | `agents/checkpointer.py` |
| Tool 层与工具分类 | `agents/tools/query|preview|execute` |
| 风险策略 | `agents/risk/`（policy / classifier / profile） |
| Agent Service | `agents/agentservice/`（runner / resumer） |
| Event Publisher / SSE | `agents/events/`、`schemas/sse.py`、前端 `api/agentSse.ts` |
| 审计 | `agents/audit/` |
| Agent API | `api/routes/agent.py`、`schemas/agent.py` |
| 复用业务 Service | `services/agent_service/` 薄适配、`agents/tools/` 调用层 |
| 前端状态流 | `composables/useAgentChat.ts`、`stores/agent.ts`、`components/chat/*` |

#### 实施顺序对应的目录推进

- **阶段一**：`agents/factory.py`、`agents/context.py`、`agents/checkpointer.py`、`agents/errors.py`、`schemas/agent.py`、`schemas/sse.py`、`api/routes/agent.py`。
- **阶段二**：`agents/tools/query/` 全部 + `agents/graph/{state,nodes,tool_router}.py` + `agents/events/` + `agents/audit/` + 前端 `agentSse.ts`、`useAgentChat.ts`。
- **阶段三**：`agents/tools/preview/scenes.py` + `agents/tools/execute/scenes.py` + `agents/risk/` + `agents/agentservice/resumer.py` + `agents/graph/{risk_node,approval,execute}.py` + 前端确认卡片。
- **阶段四**：`agents/tools/preview/automations.py` + `agents/tools/execute/automations.py` + 审计补全。
- **阶段五**：`agents/checkpointer.py` 生产化、真实设备接入与状态回读（不在本目录新增业务模型，由既有服务扩展）。

---

## 3. AgentContext 的接入方式

当前 `AgentContext` 已包含：

- `user_id`
- `household_id`
- `session_id`
- `auto_execute_low_risk`
- `confirm_high_risk`

建议将它作为运行时可信上下文，而不是放进模型可修改的工具参数中。

### 3.1 工具参数设计

不推荐：

```python
@tool
def list_devices(household_id: int, room: str | None = None):
    ...
```

推荐：

```python
class ListDevicesInput(BaseModel):
    room: str | None = Field(default=None, max_length=80)
    device_type: str | None = Field(default=None, max_length=32)
    status: str | None = None


def list_devices_tool(
    args: ListDevicesInput,
    context: AgentContext,
    db: Session,
):
    return list_devices_in_household(
        db=db,
        user_id=context.user_id,
        household_id=context.household_id,
        room=args.room,
        device_type=args.device_type,
        status=args.status,
    )
```

原则：

- `household_id`、`user_id`、`session_id` 从后端上下文获取；
- 模型只能填写业务筛选条件；
- 所有工具都重新做资源归属校验；
- 不能因为模型已经读取过资源，就跳过写操作前的再次校验。

### 3.2 偏好配置

用户偏好可以影响体验，但不应覆盖系统安全策略。推荐按以下规则计算最终策略：

```text
最终风险策略 = 系统策略 ∩ 家庭策略 ∩ 用户权限 ∩ 本次操作风险
```

安全默认值建议：

- 高风险操作默认必须确认；
- 配置创建、修改、删除默认必须确认；
- 未知风险按高风险处理；
- 偏好缺失或格式错误时采用更严格策略；
- 普通成员不能通过偏好关闭家庭管理员设置的确认要求。

---

## 4. Tool 设计指导

### 4.1 工具分类

| 类别 | 示例 | 初期是否开放 |
|---|---|---|
| 只读查询 | 房间、设备、场景、自动化、日志 | 是 |
| 预览分析 | 场景预览、自动化 diff、冲突检测 | 是 |
| 低风险执行 | 普通灯光或空调场景 | 谨慎开放 |
| 高风险执行 | 门锁、摄像头、安防 | 必须确认 |
| 配置变更 | 创建、修改、启停、删除自动化 | 后期开放 |
| 外部控制 | Home Assistant、MQTT、Matter | 接入后单独评估 |

### 4.2 工具返回值

工具返回值应是事实和状态，不要返回一大段自然语言。例如：

```json
{
  "ok": true,
  "operation": "scene_submission",
  "scene_id": "scene-123",
  "execution_id": "execution-456",
  "status": "submitted",
  "message": "场景执行请求已提交",
  "device_count": 3,
  "verified": false
}
```

推荐状态：

- `previewed`：只完成预览；
- `pending_confirmation`：等待确认；
- `submitted`：已提交到业务执行层；
- `running`：业务层记录为执行中；
- `verified`：已通过设备回读验证；
- `failed`：执行失败；
- `unknown`：无法确认最终状态。

在当前项目没有真实设备回读前，不能将 `submitted` 或 `running` 说成“设备已执行成功”。

### 4.3 工具限制

每个工具都应具备：

- Pydantic 参数校验；
- 最大结果数量；
- 最大执行时间；
- 明确错误码；
- 家庭和资源归属校验；
- 脱敏输出；
- 幂等策略或明确声明只读；
- 审计事件。

禁止提供以下通用工具：

- 任意 SQL；
- 任意 HTTP 请求；
- 任意 Python 执行；
- 文件读写；
- Shell 命令；
- 由模型指定的 `user_id` 或 `household_id`。

---

## 5. 推荐的 LangGraph 运行流程

### 5.1 只读请求

```text
接收用户消息
  -> 校验用户、会话和家庭
  -> 构造 AgentContext
  -> 选择模型并绑定只读工具
  -> 模型决定是否调用工具
  -> 执行工具并返回结果
  -> 模型生成回答
  -> 保存消息和运行摘要
```

### 5.2 需要确认的写请求

```text
模型提出写工具调用
  -> 后端重新读取目标资源
  -> 计算实际风险
  -> 生成结构化预览
  -> 保存 pending interrupt
  -> 推送 approval_required
  -> 等待 approve / edit / reject
       -> approve：重新校验并执行
       -> edit：校验编辑字段并重新评估风险
       -> reject：向 graph 注入拒绝结果
  -> 推送执行结果
  -> 保存审计记录
```

### 5.3 状态节点建议

可以将 graph 拆成以下节点：

- `load_context`：加载并验证可信上下文；
- `load_history`：加载当前会话消息；
- `model`：调用 ChatModel；
- `tool_router`：判断是否存在工具调用；
- `read_tool`：执行只读工具；
- `risk_check`：对写工具做后端风险判定；
- `approval_interrupt`：创建并等待确认；
- `write_tool`：执行已批准的写操作；
- `finalize`：生成最终答复和运行摘要；
- `audit`：记录运行、工具、确认和结果。

初期不必一次实现全部节点。建议先实现 `load_context -> model -> read_tool -> finalize`，再加入确认和写操作节点。

---

## 6. API 与 SSE 指导

### 6.1 不建议直接覆盖普通聊天接口

当前 `/api/chat/completions` 已用于普通模型转发，前端也按 OpenAI delta 格式解析。建议新增清晰的 agent API，避免已有客户端意外获得家庭控制能力：

```text
POST /api/agent/runs
POST /api/agent/sessions/{session_id}/decisions
GET  /api/agent/sessions/{session_id}/pending
```

如果最终必须复用 `/api/chat/completions`，应增加明确的 agent 模式和版本字段，并严格区分普通聊天与工具调用权限。

### 6.2 SSE 事件

建议统一事件结构：

```text
event: tool_started
data: {"event_id":"evt-1","run_id":"run-1","call_id":"call-1","tool":"list_devices"}
```

建议事件类型：

| 事件 | 用途 |
|---|---|
| `run_started` | agent 运行开始 |
| `message_delta` | 助手文本增量 |
| `tool_started` | 工具开始 |
| `tool_completed` | 工具成功 |
| `tool_failed` | 工具失败 |
| `approval_required` | 等待人工确认 |
| `execution_status` | 业务执行状态变化 |
| `run_completed` | 本轮结束 |
| `error` | 结构化错误 |

必须考虑：

- `event_id` 用于断线重连；
- `run_id` 区分不同运行；
- `call_id` 区分工具调用；
- 事件中不包含 API Key、JWT、堆栈和不必要的家庭敏感数据；
- 客户端取消读取不代表后端已撤销写操作；
- 前端不能通过固定步骤或文本关键词推断工具状态。

---

## 7. 模型工厂与 Provider 指导

当前模型工厂实际只构造 `ChatOpenAI`，但配置白名单包含多个 provider。使用 LangChain 时应改为明确的 adapter 结构：

```text
provider
  -> provider adapter
      -> ChatOpenAI / ChatAnthropic / ChatGoogleGenerativeAI / ...
      -> provider-specific configuration
      -> tool-calling capability check
```

每个 adapter 应明确：

- 模型名称格式；
- API Key 读取方式；
- endpoint 是否必填；
- 温度和最大 token 参数；
- 是否支持工具调用；
- 超时和重试策略；
- 错误转换规则。

建议先只支持一个经过验证的 provider，待工具调用、流式事件和异常处理稳定后再扩展其他 provider。不要仅因为配置允许某 provider，就认为它已经具备 LangChain agent 能力。

模型缓存还应考虑：

- 配置版本；
- API Key 轮换；
- 模型配置更新后的主动失效；
- 多 worker 的一致性；
- 请求超时和成本限制。

---

## 8. 与现有业务 Service 的接入方式

LangChain Tool 不应直接操作 SQLAlchemy Model。推荐建立薄适配层：

```text
LangChain Tool
  -> Agent Tool Adapter
      -> existing Service
          -> repository / SQLAlchemy
          -> household authorization
          -> validation
          -> transaction
          -> business log
```

### 8.1 设备工具

可复用：

- 设备列表和筛选；
- 设备详情；
- 设备日志；
- 设备状态和连接信息。

注意：当前 Device 模型存在家庭归属字段，工具查询必须始终以当前家庭作为过滤条件，不能只按全局 `device_id` 查询。

### 8.2 场景工具

可复用：

- 场景列表；
- 场景详情和步骤；
- 场景预览；
- 场景执行；
- 场景执行记录。

执行前必须重新读取 Scene、SceneStep 和关联设备，重新计算 `high_risk`，不能只信任模型之前看到的内容。

### 8.3 自动化工具

建议按以下顺序实现：

1. `list_automations`；
2. `get_automation`；
3. `preview_automation_change`；
4. `detect_automation_conflicts`；
5. `create_automation`；
6. `update_automation`；
7. `set_automation_enabled`；
8. `delete_automation`。

创建、更新和删除都必须经过确认。更新操作应携带版本号，发生版本冲突时重新读取并提示用户，不能静默覆盖其他修改。

---

## 9. 推荐实施阶段

### 阶段一：基础设施校正

目标：让 agent 具备可靠的运行前提。

- 确定 LangChain 和 LangGraph 版本；
- 修正 provider 配置与工厂实现不一致问题；
- 完善 `AgentContext` 的安全默认值；
- 明确 agent API 与普通聊天 API 边界；
- 修复 checkpointer 初始化和生命周期；
- 定义 Pydantic 工具输入、输出和 SSE 事件模型；
- 建立 agent 错误码和日志脱敏规则。

验收：没有工具调用时，agent 能在正确家庭上下文中稳定完成普通问答；越权家庭请求必须失败。

### 阶段二：只读工具 Agent

目标：完成第一个可用能力。

- 实现房间、设备、场景、自动化和日志查询工具；
- 每个工具复用现有 Service；
- 增加工具超时、结果数量限制和最大 graph 轮数；
- 将真实工具事件通过 SSE 推送给前端；
- 让前端展示真实工具步骤。

验收：用户可以用自然语言查询家庭状态，回答均能追溯到工具结果。

### 阶段三：场景预览与低风险执行

目标：实现受控的业务动作。

- 增加 `preview_scene`；
- 实现后端风险计算；
- 选择一个低风险场景作为试点；
- 支持幂等键和执行状态；
- 高风险和未知风险统一进入确认流程；
- 增加客户端取消、重试和断线测试。

验收：重复请求不会造成重复执行；模型无法通过修改参数绕过风险策略。

### 阶段四：自动化草案和确认写入

目标：把自然语言转成可审阅的配置。

- 结构化生成自动化草案；
- 展示配置 diff；
- 增加冲突检测和影响分析；
- 支持 approve、edit、reject；
- 将确认、执行和最终结果写入审计。

验收：用户确认前不修改自动化；编辑后的参数仍经过完整 Schema、权限和风险校验。

### 阶段五：生产化和真实设备闭环

目标：支持多实例和可验证的真实控制。

- 迁移到适合生产的 checkpointer；
- API Key 加密或接入 Secret Manager；
- 增加限流、成本预算和模型降级策略；
- 接入 Home Assistant、MQTT、Matter 或 Zigbee；
- 通过设备状态回读验证执行结果；
- 建立脱敏追踪、告警和运行回放。

---

## 10. 测试与验收建议

### 权限与安全

- 用户无法读取其他家庭的设备、场景和自动化；
- 工具参数中的家庭 ID 不会覆盖可信上下文；
- 普通成员不能执行管理员专属操作；
- 缺少或损坏偏好配置时默认采用严格策略；
- 高风险和未知风险操作必须确认；
- API Key 和内部堆栈不会进入模型上下文或 SSE。

### Agent 行为

- 模型遇到缺少参数时会追问，而不是自行补造；
- 工具返回空结果时不会臆测实体；
- 工具失败时不会生成伪成功文本；
- 超过最大工具轮数后能安全结束；
- 模型不支持工具调用时返回明确错误。

### 写操作

- approve、edit、reject、expire 和 execute 状态只能合法迁移一次；
- 重复点击确认不会重复执行；
- 资源删除或版本变化后确认会失效；
- 客户端断线重连能够恢复待确认状态；
- 业务返回 `submitted` 时，agent 不会声称设备已实际完成。

### 前端与协议

- 前端根据结构化 SSE 事件展示执行步骤；
- SSE 重连不会重复渲染工具结果；
- 普通聊天接口和 agent 接口行为清晰区分；
- 错误、确认等待和执行失败均有可读提示。

---

## 11. 首个推荐 MVP

建议将第一个 LangChain MVP 限定为：

> 在当前家庭中，根据自然语言查询房间、设备、场景和最近执行记录，并生成有证据来源的家庭状态报告。

MVP 包含：

- 一个经过验证的 ChatModel provider；
- `AgentContext`；
- 4～6 个只读工具；
- LangGraph 基础运行状态；
- 结构化工具事件 SSE；
- 会话消息保存；
- 家庭权限隔离；
- 工具调用和错误测试。

MVP 暂不包含：

- 门锁、摄像头和安防控制；
- 任意设备控制；
- 自动化直接创建和删除；
- 任意 SQL、HTTP 或 Python 工具；
- 未验证的多 provider 路由；
- 没有设备回读依据的“执行成功”结论。

完成该 MVP 后，再根据实际工具调用质量、响应时间、成本和用户反馈，决定是否进入场景执行和自动化管理阶段。
