# 设备管理后端设计文档

本文档只定义 Orion Home Assistant 项目“设备管理”模块的后端接口、输入输出和数据库设计，不包含具体实现代码。

## 统一约定

### 基础路径

所有接口统一使用 `/api` 前缀。

### 统一返回结构

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 通用错误码

| HTTP 状态码 | code | 含义 |
| --- | --- | --- |
| 400 | 40000 | 参数错误 |
| 404 | 40400 | 设备不存在 |
| 409 | 40900 | 设备重复 |
| 500 | 50000 | 服务器错误 |

错误返回示例：

```json
{
  "code": 40400,
  "message": "设备不存在",
  "data": null
}
```

### 设备类型

```text
light
air_conditioner
lock
camera
sensor
socket
curtain
```

### 设备状态

```text
online
offline
warning
running
```

### 接入平台

```text
Home Assistant
Matter
Zigbee
MQTT
```

## 数据库设计

### device

设备主表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | integer | PK, autoincrement | 主键 |
| device_id | varchar(64) | UNIQUE, NOT NULL, INDEX | 平台侧设备唯一标识 |
| name | varchar(80) | NOT NULL | 设备名称 |
| room | varchar(80) | NOT NULL, INDEX | 所属房间 |
| type | varchar(32) | NOT NULL, INDEX | 设备类型 |
| brand | varchar(64) | NOT NULL | 品牌 |
| status | varchar(32) | NOT NULL, INDEX | 设备状态 |
| connection | varchar(32) | NOT NULL, INDEX | 接入方式或平台 |
| firmware | varchar(64) | NOT NULL | 固件版本 |
| image_url | varchar(255) | NULL | 设备图片地址 |
| last_online | datetime | NULL | 最后在线时间 |
| created_at | datetime | NOT NULL | 创建时间 |
| updated_at | datetime | NOT NULL | 更新时间 |

### device_group

设备分组表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | integer | PK, autoincrement | 主键 |
| name | varchar(80) | NOT NULL | 分组名称 |
| description | text | NULL | 分组描述 |
| created_at | datetime | NOT NULL | 创建时间 |

### device_log

设备操作日志表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | integer | PK, autoincrement | 主键 |
| device_id | integer | FK device.id, INDEX | 设备主键 |
| action | varchar(64) | NOT NULL | 操作类型 |
| message | text | NOT NULL | 日志内容 |
| created_at | datetime | NOT NULL | 创建时间 |

## 1. 获取设备列表

接口名称：获取设备列表

接口地址：`/api/devices`

请求方式：`GET`

输入参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 10 |
| keyword | string | 否 | 搜索设备名称或品牌 |
| type | string | 否 | 设备类型筛选 |
| status | string | 否 | 设备状态筛选 |
| room | string | 否 | 房间筛选 |

请求示例：

```http
GET /api/devices?page=1&page_size=10&keyword=空调&type=air_conditioner&status=running&room=主卧
```

数据库操作：

查询 `device` 表，根据 `keyword`、`type`、`status`、`room` 组合过滤；按 `updated_at` 倒序排序；使用 `page` 和 `page_size` 分页；同时统计符合条件的总数。

输出：

```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "name": "主卧空调",
      "room": "主卧",
      "type": "air_conditioner",
      "brand": "Orion",
      "status": "running",
      "last_online": "2026-08-01T10:20:00+08:00"
    }
  ]
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total": 100,
    "items": [
      {
        "id": 1,
        "name": "主卧空调",
        "room": "主卧",
        "type": "air_conditioner",
        "brand": "Orion",
        "status": "running",
        "last_online": "2026-08-01T10:20:00+08:00"
      }
    ]
  }
}
```

错误码：`400` 参数错误，`500` 服务器错误。

## 2. 获取设备详情

接口名称：获取设备详情

接口地址：`/api/devices/{id}`

请求方式：`GET`

输入参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 设备主键 ID |

请求示例：

```http
GET /api/devices/1
```

数据库操作：

查询 `device` 表获取设备详情；查询 `device_log` 表获取该设备最近日志。

输出：

```json
{
  "id": 1,
  "device_id": "ha-climate-main-bedroom",
  "name": "主卧空调",
  "room": "主卧",
  "type": "air_conditioner",
  "brand": "Orion",
  "status": "running",
  "connection": "Home Assistant",
  "firmware": "2.4.1",
  "image_url": "/uploads/devices/ac.png",
  "last_online": "2026-08-01T10:20:00+08:00",
  "created_at": "2026-08-01T09:00:00+08:00",
  "updated_at": "2026-08-01T10:20:00+08:00",
  "logs": [
    {
      "id": 8,
      "device_id": 1,
      "action": "sync",
      "message": "Home Assistant 平台同步完成",
      "created_at": "2026-08-01T10:20:00+08:00"
    }
  ]
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "device_id": "ha-climate-main-bedroom",
    "name": "主卧空调",
    "room": "主卧",
    "type": "air_conditioner",
    "brand": "Orion",
    "status": "running",
    "connection": "Home Assistant",
    "firmware": "2.4.1",
    "image_url": "/uploads/devices/ac.png",
    "last_online": "2026-08-01T10:20:00+08:00",
    "created_at": "2026-08-01T09:00:00+08:00",
    "updated_at": "2026-08-01T10:20:00+08:00",
    "logs": []
  }
}
```

错误码：`400` 参数错误，`404` 设备不存在，`500` 服务器错误。

## 3. 添加设备

接口名称：添加设备

接口地址：`/api/devices`

请求方式：`POST`

输入参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 设备名称 |
| room | string | 是 | 所属房间 |
| type | string | 是 | 设备类型 |
| brand | string | 是 | 品牌 |
| connection | string | 是 | 接入平台 |
| device_id | string | 否 | 平台侧设备 ID，不传则后端生成 |
| firmware | string | 否 | 固件版本，默认 `1.0.0` |
| image_url | string | 否 | 设备图片地址 |

请求示例：

```json
{
  "name": "客厅灯带",
  "room": "客厅",
  "type": "light",
  "brand": "Orion",
  "connection": "Matter",
  "device_id": "matter-light-living-room",
  "firmware": "1.0.3",
  "image_url": "/uploads/devices/light.png"
}
```

数据库操作：

向 `device` 表新增一条记录，默认状态为 `offline` 或由接入平台同步后更新；向 `device_log` 表写入 `create` 日志。新增前需要检查 `device.device_id` 是否重复。

输出：

创建后的设备详情。

返回示例：

```json
{
  "code": 0,
  "message": "created",
  "data": {
    "id": 12,
    "device_id": "matter-light-living-room",
    "name": "客厅灯带",
    "room": "客厅",
    "type": "light",
    "brand": "Orion",
    "status": "offline",
    "connection": "Matter",
    "firmware": "1.0.3",
    "image_url": "/uploads/devices/light.png",
    "last_online": null,
    "created_at": "2026-08-01T11:00:00+08:00",
    "updated_at": "2026-08-01T11:00:00+08:00"
  }
}
```

错误码：`400` 参数错误，`409` 设备重复，`500` 服务器错误。

## 4. 更新设备

接口名称：更新设备

接口地址：`/api/devices/{id}`

请求方式：`PUT`

输入参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 设备主键 ID |
| name | string | 否 | 设备名称 |
| room | string | 否 | 所属房间 |
| type | string | 否 | 设备类型 |
| brand | string | 否 | 品牌 |
| status | string | 否 | 设备状态 |
| connection | string | 否 | 接入平台 |
| firmware | string | 否 | 固件版本 |
| image_url | string | 否 | 设备图片地址 |

请求示例：

```json
{
  "name": "主卧空调",
  "room": "主卧",
  "status": "online",
  "firmware": "2.4.2"
}
```

数据库操作：

查询 `device` 表确认设备存在；更新传入字段；更新 `updated_at`；当状态变为 `online` 或 `running` 时更新 `last_online`；向 `device_log` 表写入 `update` 日志。

输出：

更新后的设备详情。

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "device_id": "ha-climate-main-bedroom",
    "name": "主卧空调",
    "room": "主卧",
    "type": "air_conditioner",
    "brand": "Orion",
    "status": "online",
    "connection": "Home Assistant",
    "firmware": "2.4.2",
    "image_url": "/uploads/devices/ac.png",
    "last_online": "2026-08-01T11:10:00+08:00",
    "created_at": "2026-08-01T09:00:00+08:00",
    "updated_at": "2026-08-01T11:10:00+08:00"
  }
}
```

错误码：`400` 参数错误，`404` 设备不存在，`500` 服务器错误。

## 5. 删除设备

接口名称：删除设备

接口地址：`/api/devices/{id}`

请求方式：`DELETE`

输入参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 设备主键 ID |

请求示例：

```http
DELETE /api/devices/12
```

数据库操作：

查询 `device` 表确认设备存在；删除设备；级联删除或同步清理 `device_log` 中该设备日志。若需要保留审计日志，则可改为软删除字段 `deleted_at`，当前设计按硬删除处理。

输出：

```json
null
```

返回示例：

```json
{
  "code": 0,
  "message": "deleted",
  "data": null
}
```

错误码：`400` 参数错误，`404` 设备不存在，`500` 服务器错误。

## 6. 同步设备

接口名称：同步设备

接口地址：`/api/devices/sync`

请求方式：`POST`

输入参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| platform | string | 是 | 接入平台，支持 Home Assistant、Matter、Zigbee、MQTT |

请求示例：

```json
{
  "platform": "Home Assistant"
}
```

数据库操作：

根据 `platform` 调用对应接入平台同步设备状态；新增或更新 `device` 表设备数据；写入 `device_log` 同步日志；更新设备 `status`、`firmware`、`last_online`、`updated_at` 等字段。

输出：

```json
{
  "platform": "Home Assistant",
  "synced_count": 8
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "platform": "Home Assistant",
    "synced_count": 8
  }
}
```

错误码：`400` 参数错误，`500` 服务器错误。

## 7. 查询设备日志

接口名称：查询设备日志

接口地址：`/api/devices/{id}/logs`

请求方式：`GET`

输入参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 设备主键 ID |
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 20 |

请求示例：

```http
GET /api/devices/1/logs?page=1&page_size=20
```

数据库操作：

查询 `device` 表确认设备存在；查询 `device_log` 表中该设备日志；按 `created_at` 倒序排序；分页返回。

输出：

```json
{
  "total": 2,
  "items": [
    {
      "id": 8,
      "device_id": 1,
      "action": "sync",
      "message": "Home Assistant 平台同步完成",
      "created_at": "2026-08-01T10:20:00+08:00"
    }
  ]
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total": 2,
    "items": [
      {
        "id": 8,
        "device_id": 1,
        "action": "sync",
        "message": "Home Assistant 平台同步完成",
        "created_at": "2026-08-01T10:20:00+08:00"
      }
    ]
  }
}
```

错误码：`400` 参数错误，`404` 设备不存在，`500` 服务器错误。

## 后端分层建议

建议目录：

```text
backend/app/
  models/
    device.py
  schemas/
    device.py
  api/routes/
    devices.py
  services/
    device.py
```

职责划分：

| 层级 | 职责 |
| --- | --- |
| model | 只定义 SQLAlchemy ORM 模型和表关系 |
| schema | 只定义 Pydantic 输入输出结构和字段校验 |
| route | 只处理 HTTP 请求、依赖注入、状态码和响应 |
| service | 处理数据库查询、分页、创建、更新、删除、同步和日志写入 |

实现约束：

- router 不直接写复杂数据库逻辑。
- service 不返回 ORM 对象给前端，返回前需要通过 schema 序列化。
- 使用 SQLAlchemy 2.0 写法。
- 使用 Pydantic 做请求和响应校验。
- 不把所有逻辑写入 `main.py`。
- 不重复 SQL 查询逻辑。
