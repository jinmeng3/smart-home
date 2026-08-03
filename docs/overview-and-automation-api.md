# 全屋总览与自动化：后端接口和数据库设计

本文档描述 `WholeHomeOverview.vue` 与 `AutomationCenter.vue` 后续接入后端所需的输入、输出和数据库。当前版本没有实现这些后端接口，页面使用组件内模拟数据。

## 通用约定

- 基础路径：`/api`
- 鉴权：`Authorization: Bearer <access_token>`
- 时间：ISO 8601，数据库统一存 UTC，响应按家庭时区转换
- 成功响应：`{ "data": ..., "message": "ok" }`
- 失败响应：`{ "detail": "错误说明" }`
- 数据库：沿用项目 PostgreSQL + SQLAlchemy；主键推荐 `bigint`，时间字段使用 `timestamptz`

## 全屋总览

### GET `/api/households/{household_id}/overview`

输入：路径参数 `household_id: integer`；可选查询参数 `date: YYYY-MM-DD`，不传时取家庭时区的当天。

输出：

```json
{
  "data": {
    "summary": { "device_total": 36, "device_online": 28, "running_automation_count": 8, "alert_count": 2, "monthly_energy_kwh": 32.6, "energy_saving_rate": 0.12 },
    "home_status": { "status": "normal", "people_home": 2, "temperature": 26.0, "humidity": 55, "air_quality": "excellent", "pm25": 28, "locked_count": 6, "lock_total": 6 },
    "rooms": [{ "id": 1, "name": "客厅", "device_count": 6, "light_on": 2, "light_total": 2, "temperature": 26.0, "device_summaries": ["空调 26°C 制冷", "窗帘 已关闭"] }],
    "recent_devices": [{ "id": 101, "name": "客厅吸顶灯", "room_name": "客厅", "online": true, "state_text": "亮度 80%", "updated_at": "2026-08-03T10:15:00+08:00" }],
    "activities": [{ "id": 9001, "type": "door_unlocked", "title": "门锁开启", "description": "张晓明通过指纹打开了玄关门锁", "room_name": "玄关", "occurred_at": "2026-08-03T10:15:00+08:00" }],
    "schedule": [{ "id": 31, "time": "19:00", "name": "回家模式", "description": "玄关灯亮 · 空调制冷 26°C" }],
    "alerts": [{ "id": 71, "level": "warning", "title": "厨房烟感电池电量低", "room_name": "厨房" }]
  }
}
```

### GET `/api/households/{household_id}/devices`

输入：`page`、`page_size`、`room_id`、`online`、`favorite`、`keyword` 均为可选查询参数。

输出：`{ "data": { "items": [DeviceSummary], "total": 36, "page": 1, "page_size": 20 } }`。

### POST `/api/households/{household_id}/devices/sync`

输入：无请求体。输出：`{ "data": { "job_id": "sync_01", "accepted": true } }`，HTTP 202。同步完成后通过 WebSocket/SSE 推送设备状态。

## 自动化

### GET `/api/households/{household_id}/automations`

输入：可选查询参数 `keyword`、`trigger_type`（`location|time|device_state|sensor`）、`enabled`、`page`、`page_size`。

输出：

```json
{
  "data": {
    "summary": { "enabled": 18, "total": 24, "running": 5, "executions_today": 36, "abnormal": 1 },
    "items": [{ "id": 1, "name": "回家联动", "description": "到达家 100m 内", "trigger_type": "location", "enabled": true, "device_count": 6, "updated_at": "2026-08-01T10:15:00+08:00" }],
    "total": 24
  }
}
```

### GET `/api/automations/{automation_id}`

输入：路径参数 `automation_id`。输出包含规则基本信息、`triggers`、`conditions`、按 `position` 排序的 `actions`、关联房间和设备、最近执行统计。

### POST `/api/households/{household_id}/automations`

输入：

```json
{
  "name": "回家联动",
  "description": "当家庭成员到家时执行",
  "enabled": true,
  "triggers": [{ "type": "location", "config": { "event": "enter", "radius_m": 100 } }],
  "conditions": [{ "type": "time_range", "config": { "start": "18:00", "end": "23:00" } }],
  "actions": [{ "position": 1, "type": "device_command", "device_id": 101, "config": { "command": "turn_on" } }]
}
```

输出：`{ "data": AutomationDetail, "message": "created" }`，HTTP 201。服务端校验设备属于同一家庭、位置序号不重复、配置符合对应类型 schema。

### PATCH `/api/automations/{automation_id}`

输入：创建接口字段的任意子集；更新流程项时传完整 `triggers`、`conditions` 或 `actions` 数组。输出：更新后的 `AutomationDetail`。

### PATCH `/api/automations/{automation_id}/enabled`

输入：`{ "enabled": false }`。输出：`{ "data": { "id": 1, "enabled": false } }`。

### POST `/api/automations/{automation_id}/execute`

输入：`{ "source": "manual" }`。输出：`{ "data": { "execution_id": 5001, "status": "running" } }`，HTTP 202。幂等键可由请求头 `Idempotency-Key` 传入。

### GET `/api/automations/{automation_id}/executions`

输入：`page`、`page_size`、`status`、`started_from`、`started_to`。输出执行记录列表，每项包含 `status`、`trigger_snapshot`、`duration_ms`、`error_message`、开始/结束时间。

## 数据库表

| 表 | 关键字段 | 用途 |
|---|---|---|
| `devices` | `id`, `household_id`, `room_id`, `name`, `device_type`, `online`, `state jsonb`, `favorite`, `last_seen_at` | 设备及最新状态 |
| `device_state_events` | `id`, `device_id`, `event_type`, `state jsonb`, `occurred_at` | 状态历史和首页动态 |
| `home_presence` | `id`, `household_id`, `user_id`, `status`, `detected_at` | 在家人数 |
| `alerts` | `id`, `household_id`, `device_id`, `level`, `title`, `status`, `created_at`, `resolved_at` | 告警与提醒 |
| `energy_daily` | `id`, `household_id`, `device_id nullable`, `date`, `energy_kwh`, `baseline_kwh` | 月度能耗与节能率 |
| `automations` | `id`, `household_id`, `name`, `description`, `enabled`, `created_by`, `created_at`, `updated_at`, `version` | 自动化主表 |
| `automation_triggers` | `id`, `automation_id`, `type`, `config jsonb` | 触发器；一个规则可有多个 |
| `automation_conditions` | `id`, `automation_id`, `type`, `config jsonb`, `position` | 条件判断 |
| `automation_actions` | `id`, `automation_id`, `type`, `device_id nullable`, `scene_id nullable`, `config jsonb`, `position` | 顺序执行动作 |
| `automation_executions` | `id`, `automation_id`, `source`, `status`, `trigger_snapshot jsonb`, `started_at`, `finished_at`, `duration_ms`, `error_message` | 执行历史 |
| `automation_action_results` | `id`, `execution_id`, `action_id`, `status`, `output jsonb`, `error_message`, `started_at`, `finished_at` | 单个动作执行结果 |

建议索引：`devices(household_id, online)`、`device_state_events(device_id, occurred_at desc)`、`alerts(household_id, status, created_at desc)`、`automations(household_id, enabled)`、`automation_executions(automation_id, started_at desc)`。自动化编辑用 `version` 做乐观锁，执行记录和设备事件按月分区或定期归档。

## 实时更新

建议提供 `/api/households/{household_id}/events`（SSE 或 WebSocket），事件类型包括 `device.state_changed`、`alert.created`、`automation.started`、`automation.completed`。消息输出包含 `event_id`、`type`、`occurred_at` 和 `payload`，前端据此局部刷新，不轮询整个总览接口。
