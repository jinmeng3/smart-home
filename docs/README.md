# Smart Home 后端文档

本目录以 `smarthome-api/app/api/router.py` 注册的 FastAPI 路由为准，描述当前已经实现的后端能力。交互式接口定义以运行时生成的 OpenAPI 为最终来源。

## 快速入口

- [后端开发指南](./00-backend-development.md)：安装、配置、启动、架构、认证、响应协议和数据存储。
- 启动服务后访问 `http://127.0.0.1:8000/docs` 查看 Swagger UI。
- 访问 `http://127.0.0.1:8000/openapi.json` 获取可用于类型生成的 OpenAPI 文档。

## 当前路由概览

后端当前注册 **95 个 HTTP 路由操作**，所有业务路由默认位于 `/api` 下。

| 模块 | 路由操作数 | 文档 |
|------|-----------:|------|
| 认证 | 3 | [01-auth-account.md](./01-auth-account.md) |
| 账户与偏好 | 6 | [01-auth-account.md](./01-auth-account.md) |
| 家庭 | 4 | [02-household-members.md](./02-household-members.md) |
| 家庭成员 | 4 | [02-household-members.md](./02-household-members.md) |
| 房间 | 18 | [03-rooms.md](./03-rooms.md) |
| 设备 | 11 | [04-devices.md](./04-devices.md) |
| 场景 | 18 | [05-scenes.md](./05-scenes.md) |
| 自动化 | 10 | [06-automations.md](./06-automations.md) |
| 总览、模式、巡检、日程与同步任务 | 10 | [07-overview-schedules.md](./07-overview-schedules.md) |
| AI 模型 | 6 | [08-ai-chat.md](./08-ai-chat.md) |
| 聊天 | 5 | [08-ai-chat.md](./08-ai-chat.md) |

> 同一处理函数可以注册多个兼容路径，例如设备和房间的创建、更新接口，以及聊天补全接口；表中按实际 HTTP 路由操作计数。

## 专题文档

| 文件 | 用途 | 状态 |
|------|------|------|
| [09-inferred-backend.md](./09-inferred-backend.md) | 从前端调用侧核对接口需求；状态可能随前后端对接进度变化，不替代 OpenAPI。 | 历史需求分析 |
| [10-langchain-agent.md](./10-langchain-agent.md) | LangChain 智能家居智能体的目标架构设计：目标、架构、工具、风险策略与 API 协议。 | 📝 设计稿，实现进度见 12 |
| [11-langchain-agent-guidance.md](./11-langchain-agent-guidance.md) | LangChain 实施方向与开发指导：基于当前项目能力的可落地方向、工具设计、阶段与验收。 | 🚧 实施路线指导 |
| [12-agent-review-and-roadmap.md](./12-agent-review-and-roadmap.md) | Agent 现状审查与演进路线：对照代码盘点实现差距、风险与修复建议、扩展方向、上线检查清单。 | 📋 现状审查 |
| [13-frontend-backend-roadmap.md](./13-frontend-backend-roadmap.md) | 以后端真实能力为基准，盘点前端覆盖差距，并给出分阶段任务、接口、交付物和验收标准。 | 🚧 前端实施路线 |
| [14-morphicons-migration-roadmap.md](./14-morphicons-migration-roadmap.md) | 将现有 SVG 图标分阶段迁移到 Morphicons，说明统一适配层、替换边界、验收和回滚策略。 | 📝 迁移计划 |
| [gsap-animation-optimization-roadmap.md](./gsap-animation-optimization-roadmap.md) | 基于 GSAP 官方实践盘点前端动画架构，并给出基础设施、试点、模块推广和插件评估阶段。 | 📝 优化计划 |

> Agent 相关文档关系：`10` 描述“目标设计”，`11` 给出“如何落地”，`12` 盘点“现状与差距”。
> 阅读 agent 相关文档前，请先阅读 `12` 的现状盘点，避免把设计稿当成已实现能力。

## Agent 现状提示

- `smarthome-api/app/agents/` 目前包含 `AgentContext`、system prompt、模型工厂、异常与 checkpointer 等基础设施雏形，但完整的 agent 运行链路（工具注册、LangGraph 图、人工确认 API、SSE 事件协议）尚未实现。
- 现有 `/api/chat/completions` 和 `/api/v1/chat/completions` 仍为普通模型转发接口，不是 agent 工具调用接口。
- 详细差距、风险与建议见 [12-agent-review-and-roadmap.md](./12-agent-review-and-roadmap.md)。

## 数据库模型

当前 SQLAlchemy 模型包含以下 29 张表：

| 领域 | 表 |
|------|----|
| 用户与设置 | `users`, `user_preferences`, `ai_models` |
| 家庭与成员 | `households`, `household_memberships` |
| 房间与设备 | `rooms`, `room_devices`, `room_activity_logs`, `devices`, `device_group`, `device_logs` |
| 场景 | `scenes`, `scene_steps`, `scene_rooms`, `scene_templates`, `scene_execution_logs`, `scene_execution_steps`, `scene_drafts` |
| 自动化 | `automations`, `automation_triggers`, `automation_conditions`, `automation_actions`, `automation_executions` |
| 总览与任务 | `overview_executions`, `inspection_jobs`, `household_schedules`, `device_sync_jobs` |
| 聊天 | `chat_sessions`, `chat_messages` |

应用启动时通过 `Base.metadata.create_all()` 创建缺失表；当前没有在启动流程中自动执行 Alembic 迁移。

## 文档维护约定

1. 新增或修改接口时，以路由装饰器、Pydantic Schema 和 `/openapi.json` 为准同步模块文档。
2. 请求和响应示例应保留真实字段命名；部分 Schema 使用 alias generator 输出 camelCase。
3. 已实现能力与未来设计必须明确区分，规划内容不要写入当前接口清单。
4. 删除或增加兼容路由时同步更新上方路由操作数。
