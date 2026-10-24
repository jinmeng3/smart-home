# smarthome-api

Orion Smart Home 的后端服务，基于 **FastAPI + LangGraph**，负责 Agent 编排、会话树存储、上下文压缩与设备业务接口。

## 环境要求

- Python 3.12+
- SQLite（默认，首次启动自动建表）

## 启动

```bash
uv sync                                      # 依据 uv.lock 安装依赖
uv run uvicorn app.main:app --reload --port 8000
```

不使用 uv 时：

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS / Linux:      source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

启动后：

- API 根路径：`http://localhost:8000`
- 交互式文档：`http://localhost:8000/docs`

## 配置

复制模板并按需修改：

```bash
cp .env.example .env    # Windows PowerShell: Copy-Item .env.example .env
```

关键变量说明见根目录 [README](../README.md#-配置)。生产环境务必设置 `JWT_SECRET_KEY` 与 `API_KEY_ENCRYPTION_SECRET`，并开启 `PRODUCTION_MODE`。

## 目录结构

```
app/
├── api/            # 路由、依赖注入、异常处理
├── agents/         # Agent 引擎
│   ├── agent_service/  # 运行器、恢复器、会话租约、待审批管理
│   ├── subagents/      # 漏斗路由：规则引擎、解析器、上下文层、别名索引
│   ├── graph/          # LangGraph 状态机与工具路由
│   ├── tools/          # 工具定义（execute / preview / query）
│   ├── risk/           # 风险分类与策略
│   ├── audit/          # 审计记录
│   ├── events/         # SSE 事件与流式追踪
│   └── providers/      # 模型供应商适配
├── session_tree/   # 会话树形存储
├── compaction/     # 上下文压缩编排
├── core/           # 配置
├── db/             # 数据库初始化
├── models/         # SQLAlchemy ORM 模型
├── schemas/        # Pydantic 模型
├── services/       # 业务逻辑
└── main.py         # 应用入口
```

## 运行时产物（不提交）

- `db/`：SQLite 数据库文件
- `app/uploads/`：用户上传（头像、设备图片）
- `agent_audit/`：写操作审计记录
