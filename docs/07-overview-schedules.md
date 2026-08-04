# 总览与日程模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `rooms` | 房间（关联概览中的房间列表） | 获取家庭总览 |
| `devices` | 设备（关联概览统计） | 获取家庭总览、获取家庭设备列表 |
| `automations` | 自动化规则（关联概览统计） | 获取家庭总览 |
| `overview_executions` | 模式执行记录 | 执行家庭模式 |
| `inspection_jobs` | 巡检任务 | 创建/查询巡检 |
| `household_schedules` | 家庭日程 | 保存/获取日程 |
| `device_sync_jobs` | 设备同步任务 | 创建/查询同步任务 |

---

## 1. 首页总览 (Overview)

### 1.1 获取家庭总览

- **方法**: `GET /api/households/{household_id}/overview`
- **功能**: 获取家庭概览数据，包括设备统计、环境状况、房间列表、最近设备状态
- **输入**: 路径参数 `household_id`（需是该家庭会员）
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "summary": {
        "deviceTotal": "int",
        "deviceOnline": "int",
        "runningAutomationCount": "int",
        "alertCount": "int",
        "monthlyEnergyKwh": "float",
        "energySavingRate": "float"
      },
      "homeStatus": {
        "status": "string",
        "peopleHome": "int",
        "temperature": "float",
        "humidity": "int",
        "airQuality": "string",
        "pm25": "int",
        "lockedCount": "int",
        "lockTotal": "int"
      },
      "rooms": [
        {
          "id": "int",
          "name": "string",
          "deviceCount": "int",
          "lightOn": "int",
          "lightTotal": "int",
          "temperature": "float",
          "deviceSummaries": "string[]"
        }
      ],
      "recentDevices": [
        { "id": "int", "name": "string", "roomName": "string", "online": "bool", "stateText": "string", "updatedAt": "datetime" }
      ],
      "activities": [],
      "schedule": [],
      "alerts": []
    }
  }
  ```
- **数据库**: `rooms`, `devices`, `automations`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 1.2 获取家庭设备列表

- **方法**: `GET /api/households/{household_id}/devices`
- **功能**: 获取家庭下所有设备
- **输入**: 路径参数 `household_id`
- **输出**: 同设备列表响应
- **数据库**: `devices`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 1.3 同步家庭设备（幂等）

- **方法**: `POST /api/households/{household_id}/devices/sync`
- **功能**: 创建端到端设备同步任务（按天幂等）
- **输入**: 路径参数 `household_id`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "int",
      "status": "string",
      "statistics": { "total": "int", "synced": "int" }
    }
  }
  ```
- **数据库**: `device_sync_jobs`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

---

## 2. 模式执行 (Modes)

### 2.1 执行家庭模式

- **方法**: `POST /api/overview/modes/execute`
- **功能**: 执行家庭模式（在家/离家/睡眠/访客），按房间筛选
- **输入**:
  ```json
  {
    "mode": "home|away|sleep|guest",
    "roomIds": "int[] (可选)",
    "runAutomations": "bool (可选, 默认 true)",
    "idempotencyKey": "string (1-128)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "int",
      "status": "string",
      "affectedDeviceCount": "int"
    }
  }
  ```
- **数据库**: `overview_executions`, `rooms`, `devices`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

---

## 3. 设备巡检 (Inspections)

### 3.1 创建巡检任务

- **方法**: `POST /api/inspections`
- **功能**: 创建设备巡检任务
- **输入**:
  ```json
  {
    "scope": "all|rooms|device_types",
    "roomIds": "int[] (可选)",
    "deviceTypes": "string[] (可选)",
    "checks": "string[] (必填)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "int",
      "status": "string",
      "deviceCount": "int",
      "checkedCount": "int",
      "estimatedSeconds": "int"
    }
  }
  ```
- **数据库**: `inspection_jobs`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 3.2 查询巡检任务

- **方法**: `GET /api/inspections/{inspection_id}`
- **功能**: 查询巡检任务进度
- **输入**: 路径参数 `inspection_id`
- **输出**: 同创建巡检响应
- **数据库**: `inspection_jobs`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

---

## 4. 日程管理 (Schedules)

### 4.1 保存或更新日程

- **方法**: `PUT /api/schedules/{schedule_date}`
- **功能**: 保存或更新指定日期的家庭日程（带乐观锁）
- **输入**:
  ```json
  {
    "enabled": "bool",
    "repeatDays": "int[]",
    "targets": { "roomIds": "int[]", "deviceIds": "int[]" },
    "items": [ { "time": "string", "name": "string", "detail": "string", "sceneId": "string", "position": "int", "enabled": "bool", "color": "string" } ],
    "version": "int|null (可选, 用于冲突检测)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "int",
      "scheduleDate": "date",
      "enabled": "bool",
      "repeatDays": "int[]",
      "targets": "object",
      "items": "object[]",
      "version": "int",
      "updatedAt": "datetime"
    }
  }
  ```
- **数据库**: `household_schedules`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`saveSchedule`）

### 4.2 获取日程

- **方法**: `GET /api/schedules/{schedule_date}`
- **功能**: 获取指定日期的家庭日程
- **输入**: 路径参数 `schedule_date` (date 格式)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": { "同上" } | null
  }
  ```
- **数据库**: `household_schedules`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`getSchedule`）

---

## 5. 设备同步任务 (Device Sync Jobs)

### 5.1 创建设备同步任务

- **方法**: `POST /api/device-sync-jobs`
- **功能**: 创建设备同步任务（幂等）
- **输入**:
  ```json
  {
    "scope": "string (可选, 默认 all)",
    "sources": "string[] (必填)",
    "options": "object (可选)",
    "idempotencyKey": "string (1-128)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "int",
      "status": "string",
      "statistics": "object"
    }
  }
  ```
- **数据库**: `device_sync_jobs`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 5.2 查询同步任务

- **方法**: `GET /api/device-sync-jobs/{job_id}`
- **功能**: 查询设备同步任务进度
- **输入**: 路径参数 `job_id`
- **输出**: 同创建设备同步响应
- **数据库**: `device_sync_jobs`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接