# 场景模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `scenes` | 场景信息（名称、触发类型、启用状态等） | 场景 CRUD、批量操作 |
| `scene_steps` | 场景执行步骤 | 创建/更新场景、预览 |
| `scene_templates` | 场景模板 | 模板 CRUD |
| `scene_execution_logs` | 场景执行日志 | 执行场景、统计 |
| `scene_execution_steps` | 场景执行步骤详情 | 执行场景、获取执行结果 |
| `scene_drafts` | 场景草稿 | 保存草稿 |
| `devices` | 设备（关联场景步骤中的设备匹配） | 预览模板 |

---

## 1. 场景管理 (Scenes)

### 1.1 获取场景列表

- **方法**: `GET /api/scenes`
- **功能**: 按关键字、触发类型、启用状态筛选并按自定义顺序排列场景
- **输入**: 查询参数
  - `keyword`: string (可选, 最长 100)
  - `trigger_type`: manual|schedule|location|device (可选)
  - `enabled`: all|enabled|disabled (可选, 默认 all)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "items": [
        {
          "id": "string",
          "name": "string",
          "description": "string",
          "icon": "string",
          "color": "string",
          "triggerType": "string",
          "triggerLabel": "string",
          "roomLabels": "string[]",
          "deviceCount": "int",
          "enabled": "bool",
          "recommended": "bool",
          "highRisk": "bool",
          "sortOrder": "int",
          "sourceTemplateId": "string|null",
          "createdAt": "datetime",
          "updatedAt": "datetime",
          "steps": [
            { "id": "string", "name": "string", "description": "string", "deviceId": "string", "order": "int" }
          ]
        }
      ],
      "total": "int"
    }
  }
  ```
- **数据库**: `scenes`, `scene_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.2 创建场景

- **方法**: `POST /api/scenes`
- **功能**: 创建场景及其执行步骤
- **输入**:
  ```json
  {
    "name": "string (1-80)",
    "description": "string (可选, 最长 500)",
    "icon": "string (可选, 默认 home)",
    "color": "string (可选)",
    "triggerType": "manual|schedule|location|device",
    "triggerLabel": "string (可选, 默认 手动执行)",
    "roomLabels": "string[] (可选)",
    "deviceIds": "string[] (可选)",
    "enabled": "bool (可选, 默认 true)",
    "recommended": "bool (可选, 默认 false)",
    "highRisk": "bool|null (可选)",
    "steps": [
      { "name": "string", "description": "string", "deviceId": "string", "order": "int" }
    ]
  }
  ```
- **输出**: 场景对象
- **数据库**: `scenes`, `scene_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.3 获取场景统计

- **方法**: `GET /api/scenes/summary`
- **功能**: 返回场景数量与本月执行统计
- **输入**: 无
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "enabled": "int",
      "automation": "int",
      "manual": "int",
      "monthlyExecutions": "int",
      "enabledRate": "float",
      "automationRate": "float",
      "manualRate": "float",
      "monthlyGrowthRate": "float"
    }
  }
  ```
- **数据库**: `scenes`, `scene_execution_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.4 批量更新场景顺序

- **方法**: `PATCH /api/scenes/order`
- **功能**: 在单个事务中批量更新场景顺序
- **输入**:
  ```json
  {
    "items": [
      { "id": "string", "sort_order": "int" }
    ]
  }
  ```
- **输出**:
  ```json
  { "code": 0, "message": "ok", "data": { "updated": "int" } }
  ```
- **数据库**: `scenes`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`updateSceneOrder`）

### 1.5 保存场景草稿

- **方法**: `POST /api/scenes/drafts`
- **功能**: 保存尚未发布的场景表单快照
- **输入**: 同创建场景
- **输出**:
  ```json
  {
    "code": 0,
    "message": "created",
    "data": { "draftId": "string", "updatedAt": "datetime" }
  }
  ```
- **数据库**: `scene_drafts`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.6 更新场景

- **方法**: `PUT /api/scenes/{scene_id}`
- **功能**: 覆盖场景信息及步骤
- **输入**: 同创建场景
- **输出**: 场景对象
- **数据库**: `scenes`, `scene_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`updateScene`）

### 1.7 启用/停用场景

- **方法**: `PATCH /api/scenes/{scene_id}/enabled`
- **功能**: 启用或停用场景
- **输入**:
  ```json
  { "enabled": "bool" }
  ```
- **输出**:
  ```json
  { "code": 0, "message": "ok", "data": { "id": "string", "enabled": "bool", "updatedAt": "datetime" } }
  ```
- **数据库**: `scenes`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.8 执行场景

- **方法**: `POST /api/scenes/{scene_id}/execute`
- **功能**: 校验风险并记录完整执行结果
- **输入**:
  ```json
  { "confirmHighRisk": "bool (可选, 默认 false)", "source": "string (可选, 默认 manual)" }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "executionId": "string",
      "sceneId": "string",
      "status": "string",
      "startedAt": "datetime",
      "finishedAt": "datetime|null",
      "steps": [
        { "stepId": "string", "status": "string", "message": "string|null" }
      ]
    }
  }
  ```
- **数据库**: `scene_execution_logs`, `scene_execution_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.9 复制场景

- **方法**: `POST /api/scenes/{scene_id}/copy`
- **功能**: 复制场景及全部步骤
- **输入**:
  ```json
  { "name": "string (1-80)" }
  ```
- **输出**: 场景对象
- **数据库**: `scenes`, `scene_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.10 获取场景执行日志

- **方法**: `GET /api/scenes/{scene_id}/logs`
- **功能**: 读取场景最近执行日志
- **输入**: 查询参数 `limit`: int (默认 20, 最大 100)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "items": [
        { "id": "string", "sceneId": "string", "status": "string", "startedAt": "datetime", "finishedAt": "datetime|null", "message": "string|null" }
      ]
    }
  }
  ```
- **数据库**: `scene_execution_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`getSceneLogs`）

### 1.11 预览场景

- **方法**: `POST /api/scenes/{scene_id}/preview`
- **功能**: 返回动作链，不实际控制设备
- **输入**: `{ "source": "string (可选)" }`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "sceneId": "string",
      "highRisk": "bool",
      "triggerLabel": "string",
      "steps": [
        { "stepId": "string", "name": "string", "deviceId": "string", "estimatedMs": "int", "riskLevel": "low|high" }
      ]
    }
  }
  ```
- **数据库**: `scenes`, `scene_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`previewScene`）

### 1.12 批量启用/停用场景

- **方法**: `POST /api/scenes/batch/enabled`
- **功能**: 批量启用或停用场景
- **输入**:
  ```json
  { "sceneIds": "string[] (可选, 为空则操作全部)", "enabled": "bool" }
  ```
- **输出**:
  ```json
  { "code": 0, "message": "ok", "data": { "updatedCount": "int" } }
  ```
- **数据库**: `scenes`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`batchUpdateSceneEnabled`）

### 1.13 批量设置场景定时

- **方法**: `POST /api/scenes/batch/schedule`
- **功能**: 批量设置场景的触发类型和定时描述
- **输入**:
  ```json
  {
    "sceneIds": "string[] (可选)",
    "triggerType": "manual|schedule|location|device",
    "triggerLabel": "string (1-255)"
  }
  ```
- **输出**:
  ```json
  { "code": 0, "message": "ok", "data": { "updatedCount": "int" } }
  ```
- **数据库**: `scenes`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`batchUpdateSceneSchedule`）

---

## 2. 场景模板 (Templates)

### 2.1 获取场景模板列表

- **方法**: `GET /api/scenes/templates`
- **功能**: 按关键字、分类读取可用模板
- **输入**: 查询参数
  - `keyword`: string (可选)
  - `category`: string (可选, 最长 40)
  - `limit`: int (可选, 默认 20, 最大 100)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "items": [
        {
          "id": "string",
          "name": "string",
          "description": "string",
          "icon": "string",
          "color": "string",
          "triggerType": "string",
          "triggerLabel": "string",
          "roomLabels": "string[]",
          "deviceCount": "int",
          "recommended": "bool",
          "category": "string",
          "steps": [ { "场景步骤" } ]
        }
      ]
    }
  }
  ```
- **数据库**: `scene_templates`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.2 预览模板

- **方法**: `GET /api/scenes/templates/{template_id}/preview`
- **功能**: 预览模板步骤及本地设备匹配情况
- **输入**: 路径参数 `template_id`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "templateId": "string",
      "matchedDeviceCount": "int",
      "missingDeviceCount": "int",
      "steps": [
        { "name": "string", "description": "string", "deviceId": "string", "matched": "bool" }
      ]
    }
  }
  ```
- **数据库**: `scene_templates`, `devices`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`previewSceneTemplate`）

### 2.3 使用模板创建场景

- **方法**: `POST /api/scenes/templates/{template_id}/use`
- **功能**: 复制模板数据并创建可编辑场景
- **输入**:
  ```json
  {
    "name": "string|null (可选)",
    "enabled": "bool (可选, 默认 true)",
    "deviceMapping": "object (可选)"
  }
  ```
- **输出**: 场景对象
- **数据库**: `scene_templates`, `scenes`, `scene_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

---

## 3. 场景执行查询

### 3.1 获取执行结果

- **方法**: `GET /api/scenes/executions/{execution_id}`
- **功能**: 返回执行过程及逐步状态，供前端轮询
- **输入**: 路径参数 `execution_id`
- **输出**: 同执行场景响应
- **数据库**: `scene_execution_logs`, `scene_execution_steps`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`getSceneExecution`）