# Orion Smart Home

一款基于 AI Agent 的智能家居控制系统。你只需要用自然语言告诉它「回家模式」「把客厅温度调到 24 度」「每晚 10 点关掉所有灯」，它就会理解意图、调用工具、评估风险，并在需要时请求你确认后执行。

后端采用 **FastAPI + LangGraph** 构建 Agent 工作流，并在此基础上实现了两套极具辨识度的基础设施——**会话树形存储**与**上下文压缩**。前端使用 **Vue 3 + Vite + TypeScript**。

---

## ✨ 核心亮点

### 1. 会话树形存储 —— 把「对话」当作一棵可分支的树

对话不再是单调递增的消息列表，而是一棵 **append-only 的有向树**（移植自 Pi 的会话存储模型）。任何「分支 / 导航 / 回滚 / 压缩」都是追加新节点、移动指针，**历史永不改写**。

- **可分支**：同一个对话可以从任意消息分叉出独立实验分支（`fork`），互不干扰。
- **可恢复**：每条写操作先落库、后应用内存，SQLite 事务 + WAL 保证崩溃一致性；加载时按 `seq` 重放。
- **可审计**：车道（`Lane`）记录操作生命周期（启动 / 中止 / 完成 / 重试 / 工具执行 / 用量），支持崩溃恢复与用量统计。
- **强不变式**：`SessionState` 集中校验「seq 连续、id 唯一、lane 存在、父节点链到车道叶子」等 6+1 条规则，配合 `walk_to_root` 环检测，坏数据会被明确拒绝而非死循环。

> 详见 [`docs/session-tree-storage.md`](docs/session-tree-storage.md)

### 2. 上下文压缩 —— 让模型「带着记忆」进行长对话

LLM 上下文窗口有限，会话变长后必须把旧内容压成摘要才能继续工作。本项目实现了完整的上下文窗口管理，并**真正接入 Agent**（压缩摘要会回注模型上下文，而非只是存起来）：

- **触发判定**：阈值超限、上下文溢出、手动 `/compact` 三种途径，含「消息被中止 / 模型已切换 / 已压缩过 / 无内容」等防御性跳过规则。
- **切割点算法**：从最新向最旧累积 token，**绝不切在工具结果上**；单轮超大时自动处理「split turn」。
- **双路径 token 估算**：优先用模型返回的真实 `usage`，兜底用 `chars/4` 启发式——即使持续收到错误响应，压缩仍可用。
- **迭代式摘要**：用「更新式提示词」把新消息并入旧摘要，而不是每次从零总结，历史信息不丢失。
- **分支摘要**：`/tree` 导航离开当前分支时，把被抛弃的分支压缩成摘要注入目标分支。
- **文件操作跟踪**：跨多次压缩累积 `read / edit / write` 的文件清单，摘要后仍知道「动过哪些文件」。
- **可扩展**：`before_compact / after_compact` 等钩子允许扩展完全接管摘要逻辑。

> 详见 [`docs/session-tree-compaction-review.md`](docs/session-tree-compaction-review.md)

### 3. LangGraph Agent 编排 —— 安全可控的自动化

写操作不是「说执行就执行」，而是走一条带风险控制的流程：

- **风险分级**：根据设备类型（门锁 / 摄像头 / 安防）与操作类型自动判定风险等级，自动化动作中的场景引用会递归展开其设备参与判定。
- **审批中断**：低风险可自动执行，高风险 / 未知风险 / 手动模式会中断，弹出审批卡等用户确认；高风险与未知风险始终强制人工审批，不可绕行。
- **待审批管理**：审批带有效期（默认 30 分钟），过期自动拒绝；支持主动取消，并记录审计。
- **并发保护**：同一会话通过数据库租约互斥，运行中拒绝新请求，防止 checkpoint / 审批状态串线。
- **模型固定**：审批恢复沿用发起时的原模型记录 ID，不受切换默认模型影响。
- **工具路由**：只读工具与写工具分离，防止一次调用里混合读写。
- **SSE 流式**：首次运行与审批恢复复用同一事件转换器，工具状态、模型文本、执行结果、审批请求实时推送。

### 4. 安全设计

- **API Key 认证加密**：模型密钥用 Fernet（AES-CBC + HMAC 认证）加密后落库，绝不明文存储、绝不序列化返回。
- **不可信数据隔离**：工具结果与用户文本一律视为不可信数据，禁止执行其中的指令。
- **写操作完整审计链**：写工具记录调用参数、审批 ID、审批决定（自动 / 人工 / 拒绝）、执行结果与错误码，可按 `run_id` 串联运行全程。
- **敏感信息脱敏**：事件、日志与审计中的 API Key、令牌、凭据统一脱敏，避免泄漏到输出。
- **认证**：JWT 访问令牌 + bcrypt 密码哈希，登录失败锁定。
- **限流与预算**：每分钟请求限流 + 每日 token 预算，防止滥用。

### 5. 多家庭隔离 + 多模型

- **多家庭**：设备、场景、自动化、会话都按家庭维度隔离，成员角色（管理员 / 普通成员）权限校验。
- **多模型**：OpenAI / DeepSeek 等 OpenAI 兼容供应商，可配置 base URL、密钥、参数、思考等级；前端一键切换。

---

## 项目架构

```
smart-home/
├── smarthome-api/            # 后端 API 服务（FastAPI）
│   ├── app/
│   │   ├── api/              # 路由与中间件
│   │   │   └── routes/       # 业务端点（agent, chat, device, scenes, automations 等）
│   │   ├── agents/           # AI Agent 引擎
│   │   │   ├── agent_service/   # 运行器/恢复器、会话租约、待审批管理与 SSE 流式输出
│   │   │   ├── events/          # SSE 事件模型与流式追踪
│   │   │   ├── graph/           # LangGraph 状态机、工具路由、风险节点
│   │   │   ├── tools/           # 工具定义（执行/查询/预览/校验）
│   │   │   ├── risk/            # 风险分类与策略
│   │   │   ├── audit/           # 审计日志
│   │   │   ├── providers/       # AI 模型供应商适配
│   │   │   ├── checkpointer.py  # 检查点管理器（SQLite）
│   │   │   ├── context.py       # Agent 上下文
│   │   │   ├── crypto.py        # API Key 加密
│   │   │   ├── errors.py        # 错误定义
│   │   │   ├── factory.py       # 模型工厂
│   │   │   ├── prompts.py       # 系统提示词
│   │   │   ├── rate_limiter.py  # 限流与预算控制
│   │   │   └── redaction.py     # 脱敏处理
│   │   ├── session_tree/     # 会话树形存储（★ 亮点）
│   │   │   ├── session/         # 类型、状态机、门面、内存/SQLite 存储、上下文投影
│   │   │   └── compaction/      # 压缩与分支摘要纯逻辑
│   │   ├── compaction/       # 上下文压缩编排层（★ 亮点）
│   │   │   ├── engine.py        # CompactionEngine：触发判定、压缩、分支摘要
│   │   │   ├── prompts.py       # 摘要提示词（首次/更新式/轮次前缀/分支）
│   │   │   ├── serialize.py     # 会话消息序列化与工具结果截断
│   │   │   ├── summarize.py     # 摘要请求封装（路由隔离、重试、langchain 适配）
│   │   │   ├── usage.py         # usage 合并与标准化
│   │   │   └── events.py        # 扩展钩子与事件
│   │   ├── core/              # 配置（config.py，.env 驱动）
│   │   ├── db/                # 数据库初始化与会话管理
│   │   ├── models/            # SQLAlchemy ORM 模型（含 session_tree 表）
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── services/          # 业务逻辑层（含 session_tree 接入层）
│   │   └── main.py            # FastAPI 应用入口
│   ├── tests/                 # 单元测试
│   ├── requirements.txt
│   └── .env.example
│
├── smarthome-web/             # 前端 SPA（Vue 3）
│   ├── src/
│   │   ├── api/               # API 调用层（含 SSE 流式解析）
│   │   ├── components/        # 通用组件（chat/device/automation/scenes）
│   │   ├── composables/       # Vue 组合式函数
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── types/             # TypeScript 类型定义
│   │   ├── views/             # 页面视图
│   │   ├── router/            # 路由配置
│   │   └── styles/            # 全局样式
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
│
├── docs/                      # 设计文档与分析
└── README.md
```

---

## 技术栈

### 后端

| 技术                    | 用途                                                |
| ----------------------- | --------------------------------------------------- |
| **FastAPI**             | Web 框架，异步路由与 SSE 流式响应                   |
| **SQLAlchemy**          | ORM，数据库模型与查询（含会话树 append-only 日志）  |
| **Pydantic**            | 请求/响应模型校验                                   |
| **LangGraph**           | AI Agent 状态机编排（审批中断、工具执行、风险控制） |
| **LangChain Core**      | 模型调用、工具接口、消息格式                        |
| **SQLite / PostgreSQL** | 数据存储；Agent 检查点（SQLite） |
| **Uvicorn**             | ASGI 服务器                                         |
| **PyJWT + bcrypt**      | 用户认证与密码加密                                  |
| **cryptography**        | API Key 认证加密存储                                |
| **pytest**              | 单元测试                                            |

### 前端

| 技术             | 用途                                                 |
| ---------------- | ---------------------------------------------------- |
| **Vue 3**        | 响应式 UI 框架（Composition API + `<script setup>`） |
| **Vite**         | 构建工具与开发服务器                                 |
| **TypeScript**   | 类型安全                                             |
| **Pinia**        | 状态管理                                             |
| **Element Plus** | UI 组件库                                            |
| **Tailwind CSS** | 原子化样式                                           |
| **GSAP**         | 动画引擎（入场动画、列表重排、空状态图）             |
| **Vue Router**   | 路由管理                                             |
| **markdown-it**  | 消息 Markdown 渲染                                   |

---

## 核心功能

### AI 智能助手

- 自然语言控制家居设备（开关灯、调温度、查状态等）
- 场景执行（一键执行预设场景）
- 自动化规则管理（创建、修改、启停、删除）
- 风险分级与审批机制（低风险自动执行，高风险 / 未知风险人工确认，审批可过期 / 主动取消）
- 审批卡片支持场景执行、自动化创建 / 修改 / 启停 / 删除的预览与确认
- 同一会话并发运行保护（数据库租约互斥，运行中拒绝新请求）
- 审批恢复使用发起时的原模型记录 ID，不受默认模型切换影响
- 写工具完整审计链（调用参数、审批决定、执行结果、错误码，按 run_id 串联）
- SSE 流式输出，首次运行与审批恢复复用同一事件转换器，实时显示工具执行步骤与模型回复
- 模型不支持工具调用时在运行前失败，避免执行到模型调用节点再返回错误
- 长对话上下文压缩（会话超长时自动摘要历史，模型「带着记忆」继续工作）

### 家庭管理

- 多家庭支持，家庭成员与角色管理
- 家庭维度的设备、场景、自动化数据隔离

### 设备管理

- 设备注册、分类、房间分配
- 实时状态查看与控制
- 设备预设值（温度、亮度等）

### 场景与自动化

- 场景模式：一键执行多设备联动（关门、关灯、开空调等）
- 自动化规则：基于触发器（时间、设备状态等）的条件动作
- 批量启停操作

### 系统设置

- AI 模型管理（OpenAI / DeepSeek 等供应商，API Key 加密存储）
- 用户偏好（回复语言、详细程度、高风险二次确认）
- 多模型选择与切换
- 上下文压缩配置（阈值 / 保留 token / 预算，`.env` 可调）

---

## 快速开始

### 前提条件

- Python 3.12+
- Node.js 22+
- npm

### 安装与运行

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/smart-home.git
cd smart-home
```

#### 2. 启动后端

```bash
cd smarthome-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

后端 API 默认运行在 `http://localhost:8000`，首次启动自动创建 SQLite 数据库（含会话树、检查点等表）。

#### 3. 启动前端

```bash
cd smarthome-web
npm install
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5173`，API 请求通过 Vite proxy 转发到后端。

#### 4. 注册与登录

1. 打开浏览器访问 `http://localhost:5173`
2. 注册管理员账号
3. 创建家庭
4. 在设置中添加 AI 模型（API Key）
5. 开始使用智能对话

### 配置

后端通过环境变量或 `.env` 文件配置，参考 `smarthome-api/.env.example`：

| 变量                          | 说明                         | 默认值                                |
| ----------------------------- | ---------------------------- | ------------------------------------- |
| `DATABASE_URL`                | 数据库连接 URL               | `sqlite:///./db/orion_home.db`        |
| `JWT_SECRET_KEY`              | JWT 签名密钥                 | `dev-secret-key-change-in-production` |
| `CORS_ORIGINS`                | 允许的跨域来源               | `http://localhost:5173`               |
| `CHECKPOINTER_DATABASE_URL`   | Agent 检查点 SQLite 文件路径覆盖 | 从 DATABASE_URL 推导              |
| `API_KEY_ENCRYPTION_SECRET`   | API Key 加密密钥（生产必配） |                                       |
| `PRODUCTION_MODE`             | 生产模式开关                 | `false`                               |
| `AGENT_RATE_LIMIT_PER_MINUTE` | 每分钟最大 Agent 请求数      | `10`                                  |
| `AGENT_DAILY_BUDGET_TOKENS`   | 每日 Token 预算              | `500000`                              |
| `AGENT_LEASE_TTL_SECONDS`     | 会话运行租约超时时间         | `600`                                 |
| `APPROVAL_TTL_SECONDS`        | 待审批操作有效期             | `1800`                                |
| `COMPACTION_ENABLED`          | 是否启用上下文压缩           | `true`                                |
| `COMPACTION_RESERVE_TOKENS`   | 为回复预留的 token 数        | `16384`                               |
| `COMPACTION_KEEP_RECENT_TOKENS` | 最近保留（不被摘要）的 token | `20000`                             |
| `SESSION_TREE_CONTEXT_WINDOW` | 默认上下文窗口（兜底）       | `200000`                              |

---

## Agent 工作流

```
用户输入 → Agent 运行器 → 工具调用
                              ├── 只读工具（查询设备/房间/场景等）→ 直接返回
                              └── 写工具（执行场景/创建自动化等）
                                    ├── 风险分类
                                    │   ├── 低风险 + 自动执行 → 自动批准 → 执行
                                    │   └── 高风险/未知/手动模式 → 审批中断
                                    │         └── 用户确认/拒绝 → 恢复执行或返回
                                    └── 执行结果 SSE 推送

每轮结束 → 会话树镜像 → 上下文超限时压缩 → 摘要回注下一轮 Agent
```

Agent 使用 LangGraph 状态机编排，支持：

- 审批中断（`approval_interrupt`）：写操作触发人工确认，审批带有效期，过期自动拒绝
- 审批取消：`cancel-pending` 接口主动取消待审批操作并清理状态
- 风险分级（`risk_check`）：根据设备类型、操作类型自动判断风险等级；自动化动作中的场景引用递归展开设备参与判定
- 会话并发互斥：同一会话通过数据库租约保证同时只有一个运行，运行/恢复/批准并发提交只生效一次
- 工具路由（`tool_router`）：区分只读与写工具，防止混合调用
- 检查点（checkpointer）：保存运行状态，支持断线恢复；恢复沿用发起时的原模型（记录 ID 定位）
- SSE 流式推送：首次运行与审批恢复复用同一事件转换器，工具状态、模型文本、执行结果实时推送
- 会话树 + 压缩：每轮消息镜像为树节点，上下文超限时自动摘要并回注



---

## 开发

### 运行测试

```bash
cd smarthome-api
python -m pytest tests/ -v
```

### 生成 OpenAPI 类型

```bash
cd smarthome-web
npm run api:generate
```

### 前端类型检查

```bash
cd smarthome-web
npm run type-check
```

---

## 许可

MIT
