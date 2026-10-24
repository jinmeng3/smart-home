# 后端测试

`smarthome-api/tests/` 下的测试套件覆盖 HTTP API 与 Agent 纯逻辑模块，共 **368 个用例**，全部通过内存 SQLite 运行，不依赖外部服务。

## 运行

```bash
cd smarthome-api
uv sync                 # 含 dev 依赖组（pytest / tzdata）
uv run pytest -q        # 全量
uv run pytest tests/test_rule_engine.py -q   # 单个文件
```

不使用 uv 时：

```bash
pip install -r requirements.txt pytest tzdata
python -m pytest -q
```

## 覆盖范围

| 模块 | 主要测试文件 |
| --- | --- |
| 鉴权 / 账户 / 安全设备 | `test_api_auth.py` |
| 家庭 / 成员 | `test_api_households.py` |
| 房间 / 设备 | `test_api_devices_rooms.py` |
| AI 模型配置 | `test_api_ai_model.py` |
| 自动化规则 | `test_api_automations.py` |
| 场景 | `test_api_scenes.py`、`test_scene_execute.py` |
| 聊天会话 | `test_api_chat.py` |
| 家庭概览 / 巡检 / 日程 | `test_api_overview.py` |
| 设置建议 / AI 模板 | `test_api_settings.py` |
| 会话租约与待审批 | `test_agent_lease.py` |
| 会话树存储 / 服务 | `test_session_tree_sqlite.py`、`test_session_tree_service.py` |
| 上下文压缩 | `test_compaction.py` |
| 漏斗路由 / 上下文层 | `test_funnel_router.py`、`test_context_engine.py`、`test_subagents.py` |
| 规则层 / 别名热加载 | `test_rule_engine.py`、`test_rule_layer.py`、`test_alias_hot_reload.py` |
| 夹具冒烟 | `test_smoke.py` |

另有 `tests/subagents/` 下的分层专项测试（`test_funnel_router.py`、`test_rule_engine.py`、`test_rule_layer.py`）。

## 测试隔离策略

- **数据库**：`_override_db` 把 `app.db.session.engine` 替换为内存 SQLite（共享 `StaticPool`），会话级 fixture 一次性建表；`_truncate_tables` 在每个用例结束后清空业务数据并保留结构。
- **上传 / 审计目录**：`_isolated_dirs` 在临时目录中创建，并通过 `app.dependency_overrides[get_settings]` 重定向，用完后清理。
- **登录态**：`make_user` 自动注册 + 登录（只有 login 会写入 `SecurityDevice`）。
- **HTTP 客户端**：统一使用 `fastapi.testclient.TestClient(app)`，避开 `services.*` 之间的循环导入。
- **不调用真实 LLM**：Agent 运行、AI 模板生成等需要 OpenAI 的端点只校验 schema 与权限拦截（`401` / `422` / `500`），跳过完整执行。

> 注意：测试夹具在默认配置下会创建 `app/uploads-test/` 与 `agent_audit-test/` 目录，二者已在 `.gitignore` 中忽略。

## 已知未覆盖

- `POST /api/agent/runs` 及 Agent 的 `/decisions`、`/regenerate`、`/cancel-pending`、`/run-status`：需要真实 LangGraph + LLM。
- `POST /api/chat/completions`、`/api/agent/runs` 的 SSE 流式分支。
- `GET /api/scenes/templates`：模板数据可能存在空 `device_id`，相关用例以 `pytest.skip` 处理。
- `/uploads/*` 静态资源挂载不在 API 路由范围内。

## 维护提示

- 新增端点时同步补测试，并在 [贡献指南](../../CONTRIBUTING.md) 的规范下提交。
- 涉及 SQLAlchemy 外键约束的端点，fixture 要先创建依赖行再触发请求（例如设备必须先有房间）。
- 字段别名规则因 schema 而异：先确认对应 schema 是否有 `alias_generator`，再决定请求体用 snake_case 还是 camelCase。
