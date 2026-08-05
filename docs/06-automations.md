# 自动化模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `automations` | 自动化规则（名称、优先级、冷却时间等） | 规则 CRUD、启用/禁用 |
| `automation_triggers` | 自动化触发器配置 | 创建/更新规则、批量设置定时 |
| `automation_conditions` | 自动化条件配置 | 创建/更新规则 |
| `automation_actions` | 自动化动作配置 | 创建/更新规则 |
| `automation_executions` | 自动化执行记录 | 执行规则、查询执行记录 |

---

## 1. 自动化规则管理 (Automations)

### 1.1 获取自动化规则列表

- **方法**: `GET /api/households/{household_id}/automations`
- **功能**: 按关键字、触发类型、启用状态分页筛选自动化规则
- **输入**: 查询参数
  - `keyword`: string (可选)
  - `trigger_type`: string (可选)
  - `enabled`: bool (可选)
  - `page`: int (默认 1)
  - `page_size`: int (默认 20, 最大 100)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "summary": {
        "enabled": "int",
        "total": "int",
        "running": "int",
        "executionsToday": "int",
        "abnormal": "int"
      },
      "items": [
        {
          "id": "int",
          "name": "string",
          "description": "string",
          "triggerType": "string",
          "enabled": "bool",
          "deviceCount": "int",
          "updatedAt": "datetime"
        }
      ],
      "total": "int"
    }
  }
  ```
- **数据库**: `automations`, `automation_triggers`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`listAutomations`）

### 1.2 创建自动化规则

- **方法**: `POST /api/households/{household_id}/automations`
- **功能**: 创建自动化规则
- **输入**:
  ```json
  {
    "name": "string (1-30)",
    "description": "string (可选, 最长 100)",
    "enabled": "bool (可选, 默认 true)",
    "triggers": [
      { "type": "string", "config": "object" }
    ],
    "conditions": [
      { "type": "string", "config": "object", "position": "int (可选)" }
    ],
    "actions": [
      { "type": "string", "config": "object", "position": "int", "deviceId": "int|null", "sceneId": "string|null" }
    ],
    "priority": "int (可选, 1-3, 默认 2)",
    "cooldownSeconds": "int (可选, 默认 0)",
    "delaySeconds": "int (可选, 默认 0)",
    "note": "string (可选, 最长 100)"
  }
  ```
- **输出**: 自动化规则对象
- **数据库**: `automations`, `automation_triggers`, `automation_conditions`, `automation_actions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`createAutomation`）

### 1.3 获取自动化规则详情

- **方法**: `GET /api/automations/{automation_id}`
- **功能**: 读取自动化规则完整信息
- **输入**: 路径参数 `automation_id`
- **输出**: 自动化规则对象（含 triggers, conditions, actions）
- **数据库**: `automations`, `automation_triggers`, `automation_conditions`, `automation_actions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`getAutomation`）

### 1.4 更新自动化规则

- **方法**: `PATCH /api/automations/{automation_id}`
- **功能**: 部分更新自动化规则
- **输入**: 同创建，但所有字段可选
- **输出**: 更新后的自动化规则对象
- **数据库**: `automations`, `automation_triggers`, `automation_conditions`, `automation_actions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`updateAutomation`）

### 1.5 启用/停用自动化规则

- **方法**: `PATCH /api/automations/{automation_id}/enabled`
- **功能**: 切换自动化规则的启用状态
- **输入**:
  ```json
  { "enabled": "bool" }
  ```
- **输出**:
  ```json
  { "code": 0, "message": "ok", "data": { "id": "int", "enabled": "bool" } }
  ```
- **数据库**: `automations`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`toggleAutomationEnabled`）

### 1.6 执行自动化规则

- **方法**: `POST /api/automations/{automation_id}/execute`
- **功能**: 手动触发自动化规则执行
- **输入**:
  ```json
  { "source": "string (可选, 默认 manual)" }
  ```
- **头部**: `Idempotency-Key: string (可选)`
- **输出**:
  ```json
  { "code": 0, "message": "ok", "data": { "executionId": "int", "status": "string" } }
  ```
- **数据库**: `automation_executions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`executeAutomation`）

### 1.7 获取执行记录

- **方法**: `GET /api/automations/{automation_id}/executions`
- **功能**: 分页查询自动化规则的执行记录
- **输入**: 查询参数
  - `page`: int (默认 1)
  - `page_size`: int (默认 20, 最大 100)
  - `status`: string (可选)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "total": "int",
      "items": [
        {
          "id": "int",
          "status": "string",
          "source": "string",
          "triggerSnapshot": "object",
          "durationMs": "int|null",
          "errorMessage": "string|null",
          "startedAt": "datetime",
          "finishedAt": "datetime|null"
        }
      ]
    }
  }
  ```
- **数据库**: `automation_executions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`listAutomationExecutions`）

### 1.8 批量启用自动化规则

- **方法**: `POST /api/automations/batch-enable`
- **功能**: 批量启用指定规则并可选立即执行
- **输入**:
  ```json
  {
    "ruleIds": "int[]",
    "executeNow": "bool (可选, 默认 false)",
    "executionIntervalSeconds": "int (可选, 默认 0)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "updatedCount": "int",
      "unchangedCount": "int",
      "executionBatchId": "string|null"
    }
  }
  ```
- **数据库**: `automations`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`batchEnableAutomations`）

### 1.9 批量设置定时

- **方法**: `PUT /api/automations/schedules/batch`
- **功能**: 批量设置自动化规则的定时触发配置
- **输入**:
  ```json
  {
    "ruleIds": "int[]",
    "timezone": "string (1-64)",
    "time": "string (HH:MM 或 HH:MM:SS)",
    "weekdays": "int[]",
    "frequency": "daily|weekly",
    "interval": "int (可选, 默认 1)"
  }
  ```
- **输出**:
  ```json
  { "code": 0, "message": "ok", "data": { "updatedCount": "int", "unchangedCount": "int" } }
  ```
- **数据库**: `automations`, `automation_triggers`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`batchSetAutomationSchedule`）