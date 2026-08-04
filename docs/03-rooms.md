# 房间模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `rooms` | 房间信息（名称、楼层、环境数据等） | 房间 CRUD、设备状态更新 |
| `room_devices` | 房间与设备的绑定关系 | 设备绑定管理 |
| `room_preferences` | 房间偏好设置 | 添加/编辑房间 |
| `room_activity_logs` | 房间活动日志 | 活动日志查询 |
| `room_environment_samples` | 环境采样数据 | 环境数据查询 |
| `room_environment_reports` | 环境报告生成任务 | 报告任务管理 |
| `devices` | 设备（关联房间设备列表） | 获取房间设备列表 |
| `scenes` | 场景（关联房间场景） | 房间场景列表 |
| `scene_steps` | 场景步骤 | 预览/执行场景 |
| `scene_execution_logs` | 场景执行日志 | 执行场景 |
| `scene_execution_steps` | 场景执行步骤详情 | 执行场景 |

---

## 1. 房间管理 (Rooms)

### 1.1 列出房间

- **方法**: `GET /api/rooms`
- **功能**: 按楼层和房间类型筛选当前用户所在家庭的房间列表
- **输入**: 查询参数
  - `floor`: string (可选) — 楼层筛选
  - `room_type`: string (可选) — 房间类型筛选
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "items": [
        {
          "id": "int",
          "name": "string",
          "floor": "string",
          "roomType": "string",
          "imageUrl": "string|null",
          "icon": "string",
          "themeColor": "string",
          "version": "int",
          "area": "float",
          "comfort": "int",
          "temperature": "float",
          "humidity": "int",
          "pm25": "int",
          "illuminance": "int",
          "noise": "int",
          "deviceCount": "int",
          "onlineCount": "int",
          "deviceStates": "object",
          "updatedAt": "datetime"
        }
      ],
      "total": "int"
    }
  }
  ```
- **数据库**: `rooms`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.2 添加房间

- **方法**: `POST /api/rooms`
- **功能**: 在当前用户默认家庭中创建房间
- **输入**:
  ```json
  {
    "name": "string (1-80)",
    "floor": "string (可选, 默认 1F)",
    "room_type": "string (可选, 默认 living)",
    "icon": "string (可选, 枚举值)",
    "theme_color": "string (可选, 默认 #3478f6)",
    "device_ids": "int[] (可选)",
    "preferences": {
      "pin_common_devices": "bool",
      "show_environment": "bool",
      "show_scene_entry": "bool"
    },
    "version": "int|null (可选)"
  }
  ```
- **输出**: 单个房间信息
- **数据库**: `rooms`, `room_devices`, `room_preferences`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 1.3 编辑房间

- **方法**: `PUT /api/rooms/{room_id}`
- **功能**: 覆盖更新房间信息
- **输入**: 同添加房间
- **输出**: 单个房间信息
- **数据库**: `rooms`, `room_devices`, `room_preferences`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 1.4 更新房间设备状态

- **方法**: `PATCH /api/rooms/{room_id}/device`
- **功能**: 更新房间内单个设备的状态值，并记录活动日志
- **输入**:
  ```json
  {
    "device": "string (1-40)",
    "value": "bool|int|string"
  }
  ```
- **输出**: 更新后的房间信息
- **数据库**: `rooms`（更新 `device_states` JSON）、`room_activity_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.5 快捷操作

- **方法**: `POST /api/rooms/{room_id}/quick-action`
- **功能**: 一键操作（全灯、空调、窗帘），并记录活动日志
- **输入**:
  ```json
  {
    "action": "all_lights|air_conditioner|curtains"
  }
  ```
- **输出**: 更新后的房间信息
- **数据库**: `rooms`（更新 `device_states`）、`room_activity_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

---

## 2. 房间日志

### 2.1 获取房间活动日志

- **方法**: `GET /api/rooms/{room_id}/logs`
- **功能**: 分页查询房间活动日志，支持日期范围和关键字筛选
- **输入**: 查询参数
  - `date_from`: date (可选)
  - `date_to`: date (可选)
  - `keyword`: string (可选)
  - `page`: int (默认 1)
  - `page_size`: int (默认 10, 最大 100)
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
          "occurredAt": "datetime",
          "source": "string",
          "event": "string",
          "result": "string",
          "durationMs": "int|null",
          "deviceId": "int|null",
          "deviceName": "string|null",
          "tags": "string[]",
          "detail": "object"
        }
      ]
    }
  }
  ```
- **数据库**: `room_activity_logs`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

---

## 3. 房间设备绑定

### 3.1 获取房间设备列表

- **方法**: `GET /api/rooms/{room_id}/devices`
- **功能**: 按关键字、类型、状态筛选房间内的绑定设备
- **输入**: 查询参数
  - `keyword`: string (可选)
  - `type`: string (可选)
  - `status`: string (可选)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "items": [
        {
          "id": "int",
          "name": "string",
          "type": "string",
          "brand": "string",
          "status": "string",
          "group": "string",
          "favorite": "bool",
          "sortOrder": "int"
        }
      ],
      "total": "int"
    }
  }
  ```
- **数据库**: `room_devices`, `devices`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 3.2 替换房间设备绑定

- **方法**: `PUT /api/rooms/{room_id}/devices`
- **功能**: 全量替换房间的设备绑定关系
- **输入**:
  ```json
  {
    "devices": [
      {
        "device_id": "int",
        "group": "string (可选, 默认 未分组)",
        "favorite": "bool (可选, 默认 false)",
        "sort_order": "int (可选, 默认 0)"
      }
    ]
  }
  ```
- **输出**: 房间设备列表
- **数据库**: `room_devices`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 3.3 编辑房间设备元信息

- **方法**: `PATCH /api/rooms/{room_id}/devices/{device_id}`
- **功能**: 更新绑定设备的分组、收藏状态、排序
- **输入**:
  ```json
  {
    "group": "string|null (可选)",
    "favorite": "bool|null (可选)",
    "sort_order": "int|null (可选)"
  }
  ```
- **输出**: 房间设备列表
- **数据库**: `room_devices`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

---

## 4. 房间环境

### 4.1 获取最新环境数据

- **方法**: `GET /api/rooms/{room_id}/environment/latest`
- **功能**: 获取房间最新的环境监测数据
- **输入**: 路径参数 `room_id`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "temperature": "float",
      "humidity": "int",
      "pm25": "int",
      "illuminance": "int",
      "noise": "int",
      "comfort": "int",
      "sampledAt": "datetime"
    }
  }
  ```
- **数据库**: `room_environment_samples`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 4.2 获取环境趋势数据

- **方法**: `GET /api/rooms/{room_id}/environment/trends`
- **功能**: 获取指定指标的历史趋势数据
- **输入**: 查询参数
  - `metrics`: string (可选, 默认 `temperature,humidity`)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "metrics": ["string"],
      "items": [
        { "sampledAt": "datetime", "values": { "temperature": 0, "humidity": 0 } }
      ]
    }
  }
  ```
- **数据库**: `room_environment_samples`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 4.3 创建环境报告任务

- **方法**: `POST /api/rooms/{room_id}/environment/reports`
- **功能**: 创建环境报告生成任务
- **输入**: 路径参数 `room_id`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "taskId": "string",
      "status": "string",
      "downloadUrl": "string|null"
    }
  }
  ```
- **数据库**: `room_environment_reports`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 4.4 查询环境报告任务

- **方法**: `GET /api/environment/reports/{task_id}`
- **功能**: 查询环境报告生成任务的进度和下载地址
- **输入**: 路径参数 `task_id`
- **输出**: 同创建报告响应
- **数据库**: `room_environment_reports`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

---

## 5. 房间场景

### 5.1 获取房间场景列表

- **方法**: `GET /api/rooms/{room_id}/scenes`
- **功能**: 获取适用于该房间的场景列表
- **输入**: 路径参数 `room_id`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "items": [ { "场景对象" } ],
      "total": "int"
    }
  }
  ```
- **数据库**: `scenes`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 5.2 预览房间场景执行

- **方法**: `POST /api/rooms/{room_id}/scenes/{scene_id}/preview`
- **功能**: 预览场景动作链，不实际控制设备
- **输入**: 路径参数
- **输出**: 场景预览信息
- **数据库**: `scenes`, `scene_steps`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接

### 5.3 执行房间场景

- **方法**: `POST /api/rooms/{room_id}/scenes/{scene_id}/execute`
- **功能**: 执行指定场景，并记录活动日志
- **输入**:
  ```json
  { "scope": "room|all (可选, 默认 room)", "sync_automation": "bool (可选, 默认 true)" }
  ```
- **输出**: 场景执行结果
- **数据库**: `scenes`, `scene_execution_logs`, `scene_execution_steps`, `room_activity_logs`
- **实现状态**: ✅ 后端已实现 — ❌ 前端未对接