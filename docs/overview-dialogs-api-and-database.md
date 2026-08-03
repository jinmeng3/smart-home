# 全屋总览功能弹窗：后端接口与数据写入设计

## 1. 范围

本文覆盖全屋总览页的六个弹窗：全屋模式、添加房间、全屋巡检、设备状态总览、家庭日程和同步设备。前端当前提供完整交互与本地状态反馈；正式接入时按本文接口写入 FastAPI 服务。

统一约定：接口前缀为 `/api`，请求和响应使用 JSON，字段采用 `snake_case`；响应沿用项目的 `ApiResponse<T>`，写操作要求登录用户属于目标家庭。所有写操作在单个数据库事务中完成，失败时回滚。

## 2. 接口清单

| 弹窗 | 方法与路径 | 用途 | 是否写库 |
| --- | --- | --- | --- |
| 全屋模式 | `POST /api/overview/modes/execute` | 执行场景并记录设备动作 | 是 |
| 添加房间 | `POST /api/rooms` | 新建房间并绑定已有设备 | 是 |
| 全屋巡检 | `POST /api/inspections` | 创建巡检任务 | 是 |
| 全屋巡检 | `GET /api/inspections/{id}` | 查询进度和问题 | 否 |
| 设备状态 | `GET /api/overview/devices` | 筛选、分页查询设备状态 | 否 |
| 设备状态 | `GET /api/overview/devices/export` | 导出当前筛选结果 | 否 |
| 家庭日程 | `PUT /api/schedules/{date}` | 整体保存指定日期计划 | 是 |
| 同步设备 | `POST /api/device-sync-jobs` | 创建跨平台同步任务 | 是 |
| 同步设备 | `GET /api/device-sync-jobs/{id}` | 查询同步进度与结果 | 否 |

## 3. 请求与响应

### 3.1 执行全屋模式

```json
POST /api/overview/modes/execute
{
  "mode": "home",
  "room_ids": [1, 2, 3],
  "run_automations": true,
  "idempotency_key": "uuid"
}
```

响应返回 `execution_id`、`status`、`affected_device_count` 和逐设备执行摘要。`away` 等包含门锁或摄像头动作的模式应要求二次确认令牌。服务端先校验房间归属，再创建执行记录和动作明细，提交后交由设备网关异步执行。

### 3.2 添加房间

```json
POST /api/rooms
{
  "name": "书房",
  "room_type": "study",
  "floor": "2F",
  "icon": "room",
  "icon_color": "#3478f6",
  "device_ids": [12, 18, 23]
}
```

校验规则：名称 1–20 字；同一家庭内名称不重复；`icon` 只能取前端 SVG sprite 白名单；颜色必须为允许的主题色；绑定设备必须属于同一家庭且尚未分配给其他房间。返回完整 `RoomRead`，HTTP 状态为 `201`。

### 3.3 创建巡检

```json
POST /api/inspections
{
  "scope": "all",
  "room_ids": [],
  "device_types": [],
  "checks": ["online", "battery", "network", "latency", "firmware", "alerts"]
}
```

返回 `inspection_id`、`status: queued`、`estimated_seconds`。后台任务按设备并发检查，持续更新 `checked_count`；发现问题写入巡检问题表。前端每 2 秒轮询详情，状态进入 `succeeded` 或 `failed` 后停止。

### 3.4 设备状态查询

`GET /api/overview/devices?page=1&page_size=10&room_id=&device_type=&status=&keyword=`

响应同时包含 `summary`（总数、在线、离线、告警）和 `items`。导出接口使用相同过滤参数，返回 UTF-8 BOM CSV；导出操作写审计日志，但不修改业务数据。

### 3.5 保存家庭日程

```json
PUT /api/schedules/2025-05-20
{
  "enabled": true,
  "repeat_days": [1, 2, 3, 4, 5, 6],
  "targets": { "room_ids": [1, 2], "device_ids": [3, 6] },
  "items": [
    { "id": 1, "time": "07:00", "scene_id": 2, "position": 0 },
    { "time": "19:00", "scene_id": 1, "position": 1 }
  ],
  "version": 4
}
```

使用 `version` 做乐观锁。服务端校验场景及目标归属，在事务中更新计划、删除本次缺失的旧条目并 upsert 当前条目。版本冲突返回 `409` 和服务端最新版本，避免覆盖他人修改。

### 3.6 同步设备

```json
POST /api/device-sync-jobs
{
  "scope": "all",
  "sources": ["home_assistant"],
  "options": {
    "sync_identity_and_room": true,
    "sync_battery_and_status": true,
    "discover_new_devices": true
  },
  "idempotency_key": "uuid"
}
```

返回任务 ID。同步过程按 `(household_id, source, external_id)` upsert 设备；来源短时不可用不应将所有设备立即标记为离线，需达到超时阈值。任务完成后记录新增、更新、离线和失败数量，并保留错误摘要供同步历史查看。

## 4. 数据表设计

### 4.1 扩展 `rooms`

新增 `icon VARCHAR(40) NOT NULL DEFAULT 'room'`、`icon_color VARCHAR(16) NOT NULL DEFAULT '#3478f6'`，并增加唯一索引 `uq_rooms_household_name(household_id, name)`。设备绑定通过已有 `devices.room` 迁移为推荐的 `devices.room_id` 外键；迁移期可双写并以 `room_id` 为准。

### 4.2 `overview_executions` 与 `overview_execution_steps`

- 主表：`id`、`household_id`、`mode`、`status`、`requested_by`、`idempotency_key`、`created_at`、`finished_at`。
- 明细：`execution_id`、`device_id`、`action` JSON、`status`、`error_code`、`finished_at`。
- 唯一索引：`(household_id, idempotency_key)`。

### 4.3 `inspection_jobs` 与 `inspection_issues`

- 任务：范围及检查项 JSON、状态、设备总数、已检查数、创建人和时间。
- 问题：`inspection_id`、`device_id`、`check_type`、`severity`、`message`、`resolved_at`。
- 保留 90 天；按 `household_id, created_at` 建联合索引。

### 4.4 `household_schedules` 与 `schedule_items`

- 计划：`household_id`、日期、启用状态、重复日 bitmask、目标 JSON、`version`、更新时间。
- 条目：`schedule_id`、执行时间、`scene_id`、排序位置。
- 唯一索引：`(household_id, schedule_date)`；条目唯一索引 `(schedule_id, position)`。

### 4.5 `device_sync_jobs`

字段包括家庭、来源 JSON、范围、选项 JSON、状态、统计 JSON、错误摘要、幂等键、开始/完成时间和操作人。详细设备变更复用 `device_logs`，action 使用 `sync_created`、`sync_updated`、`sync_offline`。

## 5. 后端代码落点

- `app/schemas/overview.py`：上述请求、列表摘要和任务响应模型。
- `app/models/overview.py`：执行、巡检、日程及同步任务模型。
- `app/services/overview.py`：权限校验、事务写入、任务编排和序列化。
- `app/api/routes/overview.py`：总览聚合、模式、巡检、日程和同步路由。
- `app/api/router.py`：注册 `overview.router`。
- Alembic 迁移：新增表、索引以及 `rooms` 图标字段；迁移必须支持回滚。

## 6. 一致性、安全与可观测性

- 所有资源查询必须带 `household_id`，禁止仅凭自增 ID 操作资源。
- 模式执行和同步创建接受幂等键；重复请求返回原任务。
- 门锁、摄像头和安防动作写安全审计日志，不在普通日志中记录敏感设备凭据。
- 后台任务使用短事务，外部网关调用不占用数据库事务。
- 指标至少包含任务耗时、成功率、设备失败数；日志携带 `request_id`、任务 ID 和家庭 ID。
- 建议测试：越权访问、幂等重放、日程版本冲突、部分设备失败、同步来源超时和事务回滚。
