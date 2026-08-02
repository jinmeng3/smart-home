# 场景模式页面优化接口补充

本文档补充场景模式新版页面需要的后端能力。当前前端仍使用 Mock service，后续接入真实后端时建议在 `docs/scene-mode-api-and-database.md` 的基础上增加以下接口。

## 数据库补充

沿用 SQLite 数据库 `db/orion_home.db`。

### scenes 表新增字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| sort_order | INTEGER NOT NULL DEFAULT 0 | 场景排序，数值越小越靠前 |
| room_names | TEXT NULL | 关联房间快照，JSON 字符串，例如 `["玄关","客厅"]` |
| monthly_execute_count | INTEGER NOT NULL DEFAULT 0 | 本月执行次数缓存 |
| last_executed_at | TEXT NULL | 最近一次执行时间 |
| high_risk | INTEGER NOT NULL DEFAULT 0 | 是否包含高风险动作 |

### scene_templates

推荐模板表。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | 模板 ID |
| name | TEXT NOT NULL | 模板名称 |
| description | TEXT NOT NULL | 模板描述 |
| icon | TEXT NOT NULL | 前端 SVG 图标名 |
| device_count | INTEGER NOT NULL DEFAULT 0 | 推荐关联设备数量 |
| trigger_type | TEXT NOT NULL | 触发类型 |
| steps_json | TEXT NOT NULL | 模板步骤 JSON |
| enabled | INTEGER NOT NULL DEFAULT 1 | 是否展示 |
| sort_order | INTEGER NOT NULL DEFAULT 0 | 推荐顺序 |
| created_at | TEXT NOT NULL | 创建时间 |
| updated_at | TEXT NOT NULL | 更新时间 |

### scene_execution_steps

执行日志步骤明细，用于前端展示逐步执行状态。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | 明细 ID |
| execution_id | TEXT NOT NULL | 关联 `scene_execution_logs.id` |
| step_id | TEXT NOT NULL | 关联 `scene_steps.id` |
| status | TEXT NOT NULL | `pending`、`running`、`completed`、`failed` |
| started_at | TEXT NULL | 步骤开始时间 |
| finished_at | TEXT NULL | 步骤完成时间 |
| message | TEXT NULL | 步骤结果 |

## 场景统计摘要

`GET /api/scenes/summary`

输入：无。

输出：

```json
{
  "enabled": 4,
  "automation": 3,
  "manual": 3,
  "monthlyExecutions": 128,
  "enabledRate": 66.7,
  "automationRate": 50,
  "manualRate": 50,
  "monthlyGrowthRate": 18
}
```

数据库读取：

- 从 `scenes` 统计启用、自动化、手动数量。
- 从 `scene_execution_logs` 统计当前自然月执行次数。
- 可使用 `scenes.monthly_execute_count` 做缓存，但执行成功后必须同步更新。

## 推荐模板列表

`GET /api/scenes/templates`

输入 Query：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| limit | number | 否 | 默认 4 |

输出：

```json
{
  "items": [
    {
      "id": "romantic-dinner",
      "name": "浪漫晚餐模式",
      "description": "餐厅灯光、音乐与窗帘联动",
      "icon": "light",
      "deviceCount": 6,
      "triggerType": "manual"
    }
  ]
}
```

## 从模板创建场景

`POST /api/scenes/templates/{template_id}/use`

输入 Body：

```json
{
  "name": "浪漫晚餐模式",
  "enabled": true
}
```

输出：创建后的 `Scene` 对象。

数据库写入：

- 读取 `scene_templates.steps_json`。
- 向 `scenes` 写入场景基础信息。
- 向 `scene_steps` 批量写入模板步骤。
- 写入 `scene_execution_logs` 或审计日志，记录模板导入来源。

## 场景排序

`PATCH /api/scenes/order`

输入 Body：

```json
{
  "items": [
    { "id": "home", "sortOrder": 10 },
    { "id": "away", "sortOrder": 20 }
  ]
}
```

输出：

```json
{
  "updated": 2
}
```

数据库写入：

- 批量更新 `scenes.sort_order`。
- 查询场景列表时按 `sort_order ASC, updated_at DESC` 排序。

## 预览执行流程

`POST /api/scenes/{scene_id}/preview`

输入 Body：

```json
{
  "source": "manual"
}
```

输出：

```json
{
  "sceneId": "home",
  "highRisk": false,
  "triggerLabel": "位置触发（到达“家”半径 100m）",
  "steps": [
    {
      "stepId": "home-light-entry",
      "name": "打开玄关灯",
      "deviceId": "light-entry",
      "estimatedMs": 300,
      "riskLevel": "low"
    }
  ]
}
```

用途：

- 前端点击“预览执行”时展示将要执行的动作。
- 后端不实际控制设备，只返回校验后的动作链。

## 执行状态轮询

`GET /api/scenes/executions/{execution_id}`

输入：路径参数 `execution_id`。

输出：

```json
{
  "executionId": "exec-20260802-home",
  "sceneId": "home",
  "status": "running",
  "startedAt": "2026-08-02T18:35:00+08:00",
  "finishedAt": null,
  "steps": [
    {
      "stepId": "home-light-entry",
      "status": "completed",
      "message": "打开玄关灯成功"
    },
    {
      "stepId": "home-light-living",
      "status": "running",
      "message": "正在调整亮度"
    }
  ]
}
```

数据库读取：

- 查询 `scene_execution_logs` 获取整体执行状态。
- 查询 `scene_execution_steps` 获取每一步状态。

建议：

- 初期可使用轮询。
- 后续如接入实时联动，可升级为 SSE 或 WebSocket。
