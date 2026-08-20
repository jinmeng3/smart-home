# Orion Smart Home

一款基于 AI Agent 的智能家居控制系统，支持自然语言交互、场景执行、自动化规则管理、设备控制等核心功能。后端采用 FastAPI + LangGraph 构建 Agent 工作流，前端使用 Vue 3 + Vite + TypeScript。

## 项目架构

```
smart-home/
├── smarthome-api/        # 后端 API 服务（FastAPI）
│   ├── app/
│   │   ├── api/          # 路由与中间件
│   │   │   └── routes/   # 业务端点（agent, chat, device, scenes, automations 等）
│   │   ├── agents/       # AI Agent 引擎
│   │   │   ├── agent_service/   # 运行器（runner/resumer）与 SSE 流式输出
│   │   │   ├── events/          # SSE 事件模型与流式追踪
│   │   │   ├── graph/           # LangGraph 状态机、工具路由、风险节点
│   │   │   ├── tools/           # 工具定义（执行/查询/预览/校验）
│   │   │   ├── risk/            # 风险分类与策略
│   │   │   ├── audit/           # 审计日志
│   │   │   ├── providers/       # AI 模型供应商适配
│   │   │   ├── checkpointer.py  # 检查点管理器
│   │   │   ├── context.py       # Agent 上下文
│   │   │   ├── crypto.py        # API Key 加密
│   │   │   ├── errors.py        # 错误定义
│   │   │   ├── factory.py       # 模型工厂
│   │   │   ├── prompts.py       # 系统提示词
│   │   │   ├── rate_limiter.py  # 限流与预算控制
│   │   │   └── redaction.py     # 脱敏处理
│   │   ├── core/          # 配置（config.py）
│   │   ├── db/            # 数据库初始化与会话管理
│   │   ├── models/        # SQLAlchemy ORM 模型
│   │   ├── schemas/       # Pydantic 请求/响应模型
│   │   ├── services/      # 业务逻辑层
│   │   └── main.py        # FastAPI 应用入口
│   ├── tests/             # 单元测试
│   ├── requirements.txt
│   └── .env.example
│
├── smarthome-web/         # 前端 SPA（Vue 3）
│   ├── src/
│   │   ├── api/           # API 调用层（含 SSE 流式解析）
│   │   │   └── generated/ # OpenAPI 自动生成类型
│   │   ├── components/    # 通用组件
│   │   │   ├── chat/      # 聊天相关组件（消息、审批卡、状态条等）
│   │   │   ├── device/    # 设备控制组件
│   │   │   ├── automation/ # 自动化组件
│   │   │   ├── scenes/    # 场景组件
│   │   │   └── ...
│   │   ├── composables/   # Vue 组合式函数
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── types/         # TypeScript 类型定义
│   │   ├── views/         # 页面视图
│   │   ├── router/        # 路由配置
│   │   ├── styles/        # 全局样式（Tailwind + 自定义变量）
│   │   ├── utils/         # 工具函数
│   │   └── main.ts        # 入口文件
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
│
├── docs/                  # 设计文档与分析
└── README.md
```

## 技术栈

### 后端

| 技术                    | 用途                                                |
| ----------------------- | --------------------------------------------------- |
| **FastAPI**             | Web 框架，异步路由与 SSE 流式响应                   |
| **SQLAlchemy**          | ORM，数据库模型与查询                               |
| **Pydantic**            | 请求/响应模型校验                                   |
| **LangGraph**           | AI Agent 状态机编排（审批中断、工具执行、风险控制） |
| **LangChain Core**      | 模型调用、工具接口、消息格式                        |
| **SQLite / PostgreSQL** | 数据存储与 Agent 检查点                             |
| **Uvicorn**             | ASGI 服务器                                         |
| **PyJWT + bcrypt**      | 用户认证与密码加密                                  |
| **cryptography**        | API Key 加密存储                                    |
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

## 核心功能

### AI 智能助手

- 自然语言控制家居设备（开关灯、调温度、查状态等）
- 场景执行（一键执行预设场景）
- 自动化规则管理（创建、修改、启停、删除）
- 风险分级与审批机制（低风险自动执行，高风险/未知风险人工确认）
- 审批卡片支持场景执行、自动化创建/修改/启停/删除的预览与确认
- SSE 流式输出，实时显示工具执行步骤与模型回复
- 工具执行审计日志

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

后端 API 默认运行在 `http://localhost:8000`，自动创建 SQLite 数据库。

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
| `CHECKPOINTER_TYPE`           | Agent 检查点类型             | `sqlite`                              |
| `API_KEY_ENCRYPTION_SECRET`   | API Key 加密密钥（生产必配） |                                       |
| `PRODUCTION_MODE`             | 生产模式开关                 | `false`                               |
| `AGENT_RATE_LIMIT_PER_MINUTE` | 每分钟最大 Agent 请求数      | `10`                                  |
| `AGENT_DAILY_BUDGET_TOKENS`   | 每日 Token 预算              | `500000`                              |

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
```

Agent 使用 LangGraph 状态机编排，支持：

- 审批中断（`approval_interrupt`）：写操作触发人工确认
- 风险分级（`risk_check`）：根据设备类型、操作类型自动判断风险等级
- 工具路由（`tool_router`）：区分只读与写工具，防止混合调用
- 检查点（checkpointer）：保存运行状态，支持断线恢复
- SSE 流式推送：工具状态、模型文本、执行结果实时推送

## API 概览

| 路径                                 | 方法      | 说明                     |
| ------------------------------------ | --------- | ------------------------ |
| `/api/auth/*`                        | POST      | 注册、登录、刷新令牌     |
| `/api/account/*`                     | GET/PATCH | 用户信息、头像、偏好设置 |
| `/api/households/*`                  | CRUD      | 家庭管理                 |
| `/api/households/{id}/members`       | CRUD      | 家庭成员管理             |
| `/api/rooms/*`                       | CRUD      | 房间管理                 |
| `/api/devices/*`                     | CRUD      | 设备管理                 |
| `/api/scenes/*`                      | CRUD      | 场景管理                 |
| `/api/automations/*`                 | CRUD      | 自动化规则管理           |
| `/api/chat/sessions`                 | CRUD      | 聊天会话                 |
| `/api/chat/sessions/{id}/messages`   | GET       | 聊天消息（分页）         |
| `/api/chat/completions`              | POST      | 对话补全（SSE）          |
| `/api/agent/runs`                    | POST      | 运行 Agent（SSE）        |
| `/api/agent/sessions/{id}/decisions` | POST      | 提交审批决策（SSE）      |
| `/api/agent/sessions/{id}/pending`   | GET       | 查询待确认操作           |
| `/api/ai-models/*`                   | CRUD      | AI 模型配置              |
| `/api/overview/*`                    | GET       | 家庭概览数据             |

### SSE 事件类型

| 事件                | 触发时机               |
| ------------------- | ---------------------- |
| `run_started`       | Agent 运行开始         |
| `message_delta`     | 模型文本流式输出       |
| `tool_started`      | 工具开始执行           |
| `tool_completed`    | 工具执行成功           |
| `tool_failed`       | 工具执行失败           |
| `approval_required` | 需要用户确认           |
| `execution_status`  | 写工具执行状态更新     |
| `run_completed`     | 整体运行完成（含状态） |
| `error`             | 运行时错误             |

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

## 许可

MIT
