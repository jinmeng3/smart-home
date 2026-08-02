# 场景模式接口与数据库设计

本文档描述“场景模式”后续接入后端时的接口契约。当前前端初期使用 `smarthome-web/src/services/scenes.ts` 读取 Mock 数据，真实接口可按以下输入、输出和数据库结构实现。

## 数据库

建议使用现有 SQLite 数据库 `db/orion_home.db`。

### scenes

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | 场景 ID |
| name | TEXT NOT NULL | 场景名称 |
| description | TEXT NOT NULL | 场景描述 |
| icon | TEXT NOT NULL | 图标名称，对应前端 `SvgIcon` |
| color | TEXT NOT NULL | 色彩 token 或 CSS 颜色 |
| trigger_type | TEXT NOT NULL | `manual`、`schedule`、`location`、`device` |
| trigger_label | TEXT NOT NULL | 触发条件展示文案 |
| device_count | INTEGER NOT NULL DEFAULT 0 | 关联设备数量 |
| enabled | INTEGER NOT NULL DEFAULT 1 | 1 启用，0 停用 |
| recommended | INTEGER NOT NULL DEFAULT 0 | 1 推荐，0 普通 |
| created_at | TEXT NOT NULL | 创建时间 |
| updated_at | TEXT NOT NULL | 更新时间 |

### scene_steps

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | 步骤 ID |
| scene_id | TEXT NOT NULL | 所属场景 ID，关联 `scenes.id` |
| name | TEXT NOT NULL | 步骤名称 |
| description | TEXT NOT NULL | 步骤描述 |
| device_id | TEXT NOT NULL | 关联设备 ID |
| step_order | INTEGER NOT NULL | 执行顺序 |

### scene_execution_logs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | 执行日志 ID |
| scene_id | TEXT NOT NULL | 场景 ID |
| status | TEXT NOT NULL | `running`、`enabled`、`failed` 等状态 |
| started_at | TEXT NOT NULL | 开始时间 |
| finished_at | TEXT | 完成时间 |
| message | TEXT | 执行结果或失败原因 |

## 接口

### 查询场景列表

`GET /api/scenes`

输入 Query：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 按名称、描述、触发条件搜索 |
| trigger_type | string | 否 | `manual`、`schedule`、`location`、`device` |
| enabled | string | 否 | `all`、`enabled`、`disabled` |

输出：

```json
{
  "items": [
    {
      "id": "home",
      "name": "回家模式",
      "description": "到家后自动恢复客厅照明、温度和安防状态",
      "icon": "home",
      "color": "var(--color-scene-home)",
      "triggerType": "location",
      "triggerLabel": "家庭成员到达小区",
      "deviceCount": 5,
      "enabled": true,
      "recommended": true,
      "createdAt": "2026-07-01 09:30",
      "updatedAt": "2026-08-01 18:20",
      "steps": []
    }
  ],
  "total": 1
}
```

### 创建场景

`POST /api/scenes`

输入 Body：

```json
{
  "name": "回家模式",
  "description": "到家后自动恢复客厅照明、温度和安防状态",
  "icon": "home",
  "color": "var(--color-scene-home)",
  "triggerType": "location",
  "triggerLabel": "家庭成员到达小区",
  "enabled": true,
  "recommended": true,
  "steps": [
    {
      "name": "打开玄关灯",
      "description": "玄关主灯开启",
      "deviceId": "light-entry",
      "order": 1
    }
  ]
}
```

输出：创建后的 `Scene` 对象，包含服务端生成的 `id`、`createdAt`、`updatedAt` 和步骤 `id`。

### 更新场景

`PUT /api/scenes/{scene_id}`

输入 Body：同创建场景，可覆盖基础信息和步骤。

输出：更新后的 `Scene` 对象。

### 启用或停用场景

`PATCH /api/scenes/{scene_id}/enabled`

输入 Body：

```json
{
  "enabled": true
}
```

输出：

```json
{
  "id": "home",
  "enabled": true,
  "updatedAt": "2026-08-02 18:30"
}
```

### 执行场景

`POST /api/scenes/{scene_id}/execute`

输入 Body：

```json
{
  "confirmHighRisk": true,
  "source": "manual"
}
```

输出：

```json
{
  "executionId": "exec-20260802-home",
  "sceneId": "home",
  "status": "enabled",
  "startedAt": "2026-08-02 18:35:00",
  "finishedAt": "2026-08-02 18:35:04",
  "steps": [
    {
      "stepId": "home-light-entry",
      "status": "completed",
      "message": "打开玄关灯成功"
    }
  ]
}
```

高风险动作包括门锁、安防摄像头、离家模式等。前端已在执行前显示确认，后端仍应校验 `confirmHighRisk`，避免绕过前端直接调用。

### 复制场景

`POST /api/scenes/{scene_id}/copy`

输入 Body：

```json
{
  "name": "回家模式 副本"
}
```

输出：复制后的 `Scene` 对象。

### 查看执行日志

`GET /api/scenes/{scene_id}/logs`

输入 Query：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| limit | number | 否 | 默认 20 |

输出：

```json
{
  "items": [
    {
      "id": "exec-20260802-home",
      "sceneId": "home",
      "status": "enabled",
      "startedAt": "2026-08-02 18:35:00",
      "finishedAt": "2026-08-02 18:35:04",
      "message": "执行成功"
    }
  ]
}
```
