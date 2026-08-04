# 设备模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `devices` | 设备信息（名称、类型、品牌、状态等） | 设备 CRUD、同步 |
| `device_group` | 设备分组 | 批量分配分组 |
| `device_logs` | 设备操作日志 | 操作日志查询 |

---

## 1. 设备管理 (Devices)

### 1.1 获取设备列表

- **方法**: `GET /api/devices`
- **功能**: 按关键字、类型、状态、房间分页筛选设备
- **输入**: 查询参数
  - `page`: int (默认 1)
  - `page_size`: int (默认 10, 最大 100)
  - `keyword`: string (可选, 最长 80)
  - `type`: light|air_conditioner|lock|camera|sensor|socket|curtain (可选)
  - `status`: online|offline|warning|running (可选)
  - `room`: string (可选, 最长 80)
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
          "name": "string",
          "room": "string",
          "type": "string",
          "brand": "string",
          "status": "string",
          "connection": "string",
          "firmware": "string",
          "image_url": "string|null",
          "last_online": "datetime|null"
        }
      ]
    }
  }
  ```
- **数据库**: `devices`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.2 创建设备

- **方法**: `POST /api/devices`
- **功能**: 创建设备并写入创建日志
- **输入**:
  ```json
  {
    "name": "string (1-80)",
    "room": "string (1-80)",
    "type": "light|air_conditioner|lock|camera|sensor|socket|curtain",
    "brand": "string (1-64)",
    "connection": "Home Assistant|Matter|Zigbee|MQTT",
    "device_id": "string|null (可选)",
    "firmware": "string (可选, 默认 1.0.0)",
    "image_url": "string|null (可选)"
  }
  ```
- **输出**: 设备详情
- **数据库**: `devices`, `device_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.3 同步设备

- **方法**: `POST /api/devices/sync`
- **功能**: 同步指定接入平台下的设备
- **输入**:
  ```json
  { "platform": "Home Assistant|Matter|Zigbee|MQTT" }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": { "platform": "string", "synced_count": "int" }
  }
  ```
- **数据库**: `devices`, `device_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.4 获取设备详情

- **方法**: `GET /api/devices/{device_id}`
- **功能**: 读取设备详情及最近操作日志
- **输入**: 路径参数 `device_id`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "int",
      "device_id": "string",
      "name": "string",
      "room": "string",
      "type": "string",
      "brand": "string",
      "status": "string",
      "connection": "string",
      "firmware": "string",
      "image_url": "string|null",
      "last_online": "datetime|null",
      "created_at": "datetime",
      "updated_at": "datetime",
      "logs": [
        { "id": "int", "device_id": "int", "action": "string", "message": "string", "created_at": "datetime" }
      ]
    }
  }
  ```
- **数据库**: `devices`, `device_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.5 更新设备

- **方法**: `PUT /api/devices/{device_id}`
- **功能**: 更新设备信息和在线状态
- **输入**:
  ```json
  {
    "name": "string (可选)",
    "room": "string (可选)",
    "type": "string (可选)",
    "brand": "string (可选)",
    "status": "online|offline|warning|running (可选)",
    "connection": "string (可选)",
    "firmware": "string (可选)",
    "image_url": "string|null (可选)"
  }
  ```
- **输出**: 设备详情
- **数据库**: `devices`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.6 删除设备

- **方法**: `DELETE /api/devices/{device_id}`
- **功能**: 删除设备及其关联日志
- **输入**: 路径参数 `device_id`
- **输出**: `{ "code": 0, "message": "deleted", "data": null }`
- **数据库**: `devices`, `device_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.7 获取设备操作日志

- **方法**: `GET /api/devices/{device_id}/logs`
- **功能**: 分页读取指定设备的操作日志
- **输入**: 查询参数
  - `page`: int (默认 1)
  - `page_size`: int (默认 20, 最大 100)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "total": "int",
      "items": [
        { "id": "int", "device_id": "int", "action": "string", "message": "string", "created_at": "datetime" }
      ]
    }
  }
  ```
- **数据库**: `device_logs`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.8 上传设备图片

- **方法**: `POST /api/devices/images`
- **功能**: 上传设备图片，可选关联已有设备
- **输入**: `multipart/form-data`
  - `file`: 文件 (必填)
  - `device_id`: int (可选)
- **输出**:
  ```json
  {
    "code": 0,
    "message": "uploaded",
    "data": {
      "image_url": "string",
      "original_name": "string",
      "mime_type": "string",
      "size_bytes": "int"
    }
  }
  ```
- **数据库**: `devices`（可选更新 `image_url`）
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.9 批量分配设备分组

- **方法**: `POST /api/devices/groups/assign`
- **功能**: 创建或复用分组，并将指定设备批量分配
- **输入**:
  ```json
  {
    "group": "string (1-80)",
    "device_ids": "int[] (可选)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "group_id": "int",
      "group": "string",
      "assigned_count": "int"
    }
  }
  ```
- **数据库**: `device_group`, `devices`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`batchGroupDevices`）

---

## 2. 前端调用了但后端未实现的接口

以下接口在前端 `device.ts` 中定义了调用函数，但后端无对应路由：

### 2.1 扫描设备

- **方法**: `POST /api/devices/scan`
- **前端调用**: `scanDevices`
- **输入**: `{ "platform": "string|null" }`
- **实现状态**: ❌ 后端未实现 — ✅ 前端已调用（`scanDevices`）

### 2.2 批量更新固件

- **方法**: `POST /api/devices/firmware`
- **前端调用**: `batchUpdateFirmware`
- **输入**: `{ "device_ids": "int[]", "version": "string" }`
- **实现状态**: ❌ 后端未实现 — ✅ 前端已调用（`batchUpdateFirmware`）