# Smart Home API 文档总览

> 本文档整理了 smart-home 前后端项目的所有 API 接口，按模块分类。
>
> - ✅ 后端已实现 — ✅ 前端已实现：前后端均已对接完成
> - ✅ 后端已实现 — ❌ 前端未对接：后端已实现，但前端尚未调用
> - ❌ 后端未实现 — ✅ 前端已调用：前端有调用代码，但后端无对应路由

> 各模块涉及的数据库表已分散到对应模块文档中，详见下方文件索引。

---

## 接口统计

| 模块 | 接口总数 | 前后端已完成 | 后端未对接前端 | 前端未对接后端 |
|------|---------|------------|--------------|---------------|
| 认证 (Auth) | 3 | 3 | 0 | 0 |
| 账户 (Account) | 4 | 4 | 0 | 0 |
| 家庭 (Household) | 4 | 2 | 2 | 0 |
| 成员 (Members) | 4 | 4 | 0 | 0 |
| 房间 (Rooms) | 16 | 3 | 13 | 0 |
| 设备 (Devices) | 9 | 9 | 0 | 2 |
| 场景 (Scenes) | 17 | 9 | 8 | 0 |
| 自动化 (Automations) | 9 | 9 | 0 | 0 |
| 总览/模式/巡检/同步 | 8 | 0 | 8 | 0 |
| 日程 (Schedules) | 2 | 2 | 0 | 0 |
| AI 模型 | 6 | 5 | 1 | 0 |
| 聊天 (Chat) | 5 | 4 | 1 | 0 |
| **总计** | **87** | **54** | **33** | **2** |

> 后端共有 **87** 个路由接口，其中 **54** 个已前后端对接完成，**33** 个仅后端实现。前端另有 **2** 个接口调用但后端未实现（`/api/devices/scan`、`/api/devices/firmware`）。

---

## 模块文件索引

| 文件 | 包含模块 |
|------|---------|
| [01-auth-account.md](./01-auth-account.md) | 认证 (Auth)、账户 (Account) |
| [02-household-members.md](./02-household-members.md) | 家庭 (Household)、成员 (Members) |
| [03-rooms.md](./03-rooms.md) | 房间管理、房间日志、设备绑定、环境、场景 |
| [04-devices.md](./04-devices.md) | 设备管理、图片上传、分组 |
| [05-scenes.md](./05-scenes.md) | 场景管理、模板、执行查询 |
| [06-automations.md](./06-automations.md) | 自动化规则管理 |
| [07-overview-schedules.md](./07-overview-schedules.md) | 总览、模式执行、巡检、日程、设备同步任务 |
| [08-ai-chat.md](./08-ai-chat.md) | AI 模型管理、聊天 |
| [09-inferred-backend.md](./09-inferred-backend.md) | 前端推断后端接口规范（完整清单） |
| [10-langchain-agent.md](./10-langchain-agent.md) | LangChain 智能家居智能体设计方案 |

---

## 数据库表一览

数据库表的具体说明已分散到各模块文档中，不再集中列出。

### 按模块的数据库表分布

| 模块 | 涉及的表 | 详见文档 |
|------|---------|---------|
| 认证/账户 | `users`, `auth_sessions` | [01-auth-account.md](./01-auth-account.md) |
| 家庭/成员 | `households`, `household_memberships`, `users` | [02-household-members.md](./02-household-members.md) |
| 房间 | `rooms`, `room_devices`, `room_preferences`, `room_activity_logs`, `room_environment_samples`, `room_environment_reports`, `devices`, `scenes`, `scene_steps`, `scene_execution_logs`, `scene_execution_steps` | [03-rooms.md](./03-rooms.md) |
| 设备 | `devices`, `device_group`, `device_logs` | [04-devices.md](./04-devices.md) |
| 场景 | `scenes`, `scene_steps`, `scene_templates`, `scene_execution_logs`, `scene_execution_steps`, `scene_drafts`, `devices` | [05-scenes.md](./05-scenes.md) |
| 自动化 | `automations`, `automation_triggers`, `automation_conditions`, `automation_actions`, `automation_executions` | [06-automations.md](./06-automations.md) |
| 总览/模式/巡检/同步 | `rooms`, `devices`, `automations`, `overview_executions`, `inspection_jobs`, `device_sync_jobs` | [07-overview-schedules.md](./07-overview-schedules.md) |
| 日程 | `household_schedules` | [07-overview-schedules.md](./07-overview-schedules.md) |
| AI 模型 | `ai_models` | [08-ai-chat.md](./08-ai-chat.md) |
| 聊天 | `chat_sessions`, `chat_messages` | [08-ai-chat.md](./08-ai-chat.md) |

---

## 前端已调用但后端未实现的接口

| 方法 | 路径 | 前端函数 | 说明 |
|------|------|---------|------|
| POST | `/api/devices/scan` | `scanDevices` | 扫描发现设备 |
| POST | `/api/devices/firmware` | `batchUpdateFirmware` | 批量更新设备固件 |

## 注意事项

1. **设备总数**: 后端有 9 个设备路由，前端额外调用了 `scan` 和 `firmware` 两个路由（后端未实现）。
2. **总览路由**: 后端 `overview.py` 包含了总览、模式执行、巡检、日程、设备同步任务共 10 个路由，其中日程 2 个已对接，其余 8 个尚未对接。
3. **AI 模型删除**: 后端 `DELETE /api/ai_model/model` 已实现，前端未调用。
4. **兼容路由**: 后端 `POST /api/v1/chat/completions` 是 OpenAI 兼容格式路由，前端未调用。

## 后续建议

1. **房间模块**: 后端有大量接口（环境数据、设备绑定、日志、场景操作）前端尚未对接，建议优先对接 `GET /api/rooms` 的筛选参数和 `GET /api/rooms/{id}/devices`。
2. **自动化模块**: 后端 9 个接口已有 7 个前端对接完成（列表、创建、更新、启停、执行、批量启用、批量定时），剩余 `GET /api/automations/{id}` 和 `GET /api/automations/{id}/executions` 暂未对接。
3. **总览模块**: `GET /api/households/{id}/overview` 可用于替换首页的 mock 数据。
4. **后端补全**: 实现 `POST /api/devices/scan` 和 `POST /api/devices/firmware` 两个接口，或前端移除相关调用。
