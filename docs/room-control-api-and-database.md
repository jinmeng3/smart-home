# 房间控制：接口、输入输出与数据库设计

## 1. 功能范围

房间控制页展示房间汇总、环境数据、设备状态、房间详情和联动场景。页面数据来自后端，不使用前端静态 Mock。用户必须携带登录接口返回的 Bearer Token，且只能读取自己加入家庭下的房间。

## 2. 数据流

前端输入（筛选/点击） → Vue 页面 → `/api/rooms` 接口 → FastAPI 校验登录用户 → SQLAlchemy 读写 SQLite `rooms` 表 → 统一 JSON 输出 → 页面局部更新。

开发环境数据库：`smarthome-api/db/orion_home.db`。生产环境由 `.env` 中的 `DATABASE_URL` 决定，可替换为 PostgreSQL/MySQL。

## 3. 输入什么，输出什么

所有响应外层均为：

```json
{ "code": 0, "message": "ok", "data": {} }
```

### 3.1 查询房间

`GET /api/rooms?floor=1F&room_type=living`

输入：`floor`、`room_type` 均为可选查询参数；请求头输入 `Authorization: Bearer <access_token>`。

输出：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total": 1,
    "items": [{
      "id": 1,
      "name": "客厅",
      "floor": "1F",
      "roomType": "living",
      "imageUrl": null,
      "area": 28.6,
      "comfort": 82,
      "temperature": 24.2,
      "humidity": 55,
      "pm25": 18,
      "illuminance": 320,
      "noise": 42,
      "deviceCount": 8,
      "onlineCount": 8,
      "deviceStates": { "light": true, "airConditioner": true, "curtain": true, "socket": true },
      "updatedAt": "2026-08-03T10:25:00"
    }]
  }
}
```

### 3.2 修改单个设备状态

`PATCH /api/rooms/{roomId}/device`

输入：

```json
{ "device": "light", "value": false }
```

`device` 可为页面所用的 `light`、`airConditioner`、`curtain`、`socket`；`value` 可为布尔值、数值或字符串，以便后续支持亮度、温度和模式。输出为更新后的完整房间对象，`message` 为“设备状态已更新”。

### 3.3 快捷操作

`POST /api/rooms/{roomId}/quick-action`

输入：

```json
{ "action": "all_lights" }
```

允许值：`all_lights`、`air_conditioner`、`curtains`。输出为更新后的完整房间对象，`message` 为“快捷操作已执行”。

错误输出：未登录返回 HTTP 401；无权访问或房间不属于当前用户的家庭时对外统一表现为 HTTP 404；参数不合法返回 HTTP 422。

## 4. 数据库表 `rooms`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INTEGER PK | 房间主键 |
| `household_id` | INTEGER FK | 所属家庭，删除家庭时级联删除 |
| `name` | VARCHAR(80) | 房间名称 |
| `floor` | VARCHAR(40) | 楼层 |
| `room_type` | VARCHAR(32) | living/bedroom/kitchen/study/balcony |
| `image_url` | VARCHAR(500) NULL | 房间图片地址 |
| `area` | FLOAT | 面积（平方米） |
| `comfort` | INTEGER | 舒适度 0–100 |
| `temperature` | FLOAT | 摄氏温度 |
| `humidity` | INTEGER | 相对湿度百分比 |
| `pm25` | INTEGER | PM2.5 |
| `illuminance` | INTEGER | 光照 lux |
| `noise` | INTEGER | 噪音 dB |
| `device_count` | INTEGER | 设备数 |
| `online_count` | INTEGER | 在线设备数 |
| `device_states` | TEXT(JSON) | 房间内常用设备的实时状态快照 |
| `updated_at` | DATETIME | 最后更新时间 |

`household_id` 建有索引；接口先根据 `household_memberships` 找出当前用户可访问的家庭，再限制房间查询范围。应用启动时 `Base.metadata.create_all()` 创建新表；开发模式首次运行会写入截图对应的 6 个示例房间。

## 5. 前后端字段约定

数据库与 Python 使用 snake_case（如 `room_type`），API 通过 Pydantic 自动输出 camelCase（如 `roomType`），Vue/TypeScript 全程使用 camelCase。时间为 ISO 8601 字符串，温度保留浮点数，开关状态为布尔值。

## 6. 本地运行

后端：进入 `smarthome-api`，安装 `requirements.txt` 后执行 `uvicorn app.main:app --reload`。前端：进入 `smarthome-web`，执行 `npm install`、`npm run dev`，登录后访问 `/rooms`。

## 7. 房间功能弹窗与后端写入设计

前端 `RoomControlDialogs.vue` 已实现编辑房间、添加房间、活动日志、场景切换、设备管理和环境详情六个界面。当前仅 3.1～3.3 的接口已经落地；以下接口是将弹窗从页面内交互升级为真实持久化时的后端契约。

### 7.1 新增房间

`POST /api/rooms`

```json
{
  "name": "书房",
  "floor": "2F",
  "roomType": "study",
  "icon": "room",
  "themeColor": "#2563eb",
  "deviceIds": [3, 6, 9],
  "preferences": {
    "pinCommonDevices": true,
    "showEnvironment": true,
    "showSceneEntry": true
  }
}
```

服务端必须从当前登录用户的家庭成员关系推导 `household_id`，不能接受客户端直接传入家庭主键。事务中依次写入 `rooms`、`room_devices` 和 `room_preferences`；任一设备不属于当前家庭时整体回滚并返回 HTTP 422。成功返回 HTTP 201 和完整 `RoomRead`。

### 7.2 编辑房间

`PUT /api/rooms/{roomId}`

请求体与新增房间一致，字段可全部提交。更新步骤：锁定并校验房间归属、更新 `rooms` 基础字段、删除该房间不再绑定的 `room_devices`、插入新增绑定、以 upsert 方式保存偏好，最后一次性提交事务。建议使用乐观锁字段 `version`；客户端版本落后时返回 HTTP 409。

### 7.3 房间活动日志

`GET /api/rooms/{roomId}/logs?date_from=2026-07-29&date_to=2026-08-04&type=&device_id=&keyword=&page=1&page_size=10`

输出：

```json
{
  "total": 32,
  "items": [{
    "id": 101,
    "occurredAt": "2026-08-04T10:15:32+08:00",
    "source": "manual",
    "event": "灯光开启",
    "result": "success",
    "durationMs": 300,
    "deviceId": 3,
    "deviceName": "客厅吸顶灯",
    "tags": ["灯光", "客厅"],
    "detail": { "operator": "张晓明", "channel": "app" }
  }]
}
```

设备开关、快捷操作、场景执行和环境告警成功提交后，应在同一业务事务中插入 `room_activity_logs`，避免状态已变更但日志缺失。

### 7.4 场景预览与执行

- `GET /api/rooms/{roomId}/scenes`：返回可用场景及推荐原因。
- `POST /api/rooms/{roomId}/scenes/{sceneId}/preview`：根据应用范围计算受影响设备，只读不写库。
- `POST /api/rooms/{roomId}/scenes/{sceneId}/execute`：输入 `scope` 和 `syncAutomation`，创建一次执行记录并更新设备状态。

```json
{ "scope": "room", "syncAutomation": true }
```

执行应生成唯一 `execution_id`，写入 `scene_executions` 和 `scene_execution_items`。设备指令可能由外部网关异步完成，因此主记录使用 `pending/running/succeeded/partial_failed/failed` 状态，不应把所有网络调用包在数据库长事务中。

### 7.5 房间设备管理

- `GET /api/rooms/{roomId}/devices?keyword=&type=&status=`：读取房间设备列表。
- `PUT /api/rooms/{roomId}/devices`：批量替换绑定关系。
- `PATCH /api/rooms/{roomId}/devices/{deviceId}`：修改分组、常用标记或房间内显示顺序。
- `POST /api/rooms/{roomId}/devices/batch-control`：批量开关。

批量绑定请求：

```json
{
  "devices": [
    { "deviceId": 3, "group": "灯光", "favorite": true, "sortOrder": 1 },
    { "deviceId": 6, "group": "环境", "favorite": true, "sortOrder": 2 }
  ]
}
```

`room_devices` 应对 `(room_id, device_id)` 建唯一索引。设备换房时，服务端需同时更新设备表中的房间归属，避免两个数据源不一致。

### 7.6 环境实时值、趋势和报告

- `GET /api/rooms/{roomId}/environment/latest`：返回最新五项指标与舒适度。
- `GET /api/rooms/{roomId}/environment/trends?range=today&metrics=temperature,humidity`：返回降采样趋势点。
- `POST /api/rooms/{roomId}/environment/reports`：创建导出任务，返回任务 ID。
- `GET /api/environment/reports/{taskId}`：查询生成状态和下载地址。

传感器原始数据写入 `room_environment_samples`。建议按 `(room_id, sampled_at)` 建联合索引，并按数据量设置保留策略：原始分钟数据保留 30 天，小时聚合保留 1 年。趋势接口应由后端聚合，不要把全部原始点发送给浏览器。

## 8. 新增数据表建议

| 表 | 核心字段 | 用途 |
| --- | --- | --- |
| `room_devices` | `room_id`, `device_id`, `group_name`, `favorite`, `sort_order` | 房间与设备绑定及排序 |
| `room_preferences` | `room_id`, `pin_common_devices`, `show_environment`, `show_scene_entry` | 快捷控制显示偏好 |
| `room_activity_logs` | `room_id`, `device_id`, `source`, `event`, `result`, `detail_json`, `occurred_at` | 操作与告警审计 |
| `room_environment_samples` | `room_id`, `temperature`, `humidity`, `pm25`, `illuminance`, `noise`, `sampled_at` | 环境历史数据 |
| `room_scenes` | `room_id`, `scene_id`, `scope`, `sort_order`, `enabled` | 房间可用场景 |
| `scene_executions` | `room_id`, `scene_id`, `status`, `started_at`, `finished_at` | 场景执行主记录 |
| `scene_execution_items` | `execution_id`, `device_id`, `command_json`, `status`, `error_message` | 场景设备执行明细 |

所有表均应包含创建/更新时间；审计和采样表建议使用不可变追加写。删除房间时，绑定、偏好和场景关系可级联删除，活动日志与环境历史建议软关联或归档，避免审计数据意外丢失。

## 9. 权限、校验与幂等

- 所有 `{roomId}` 接口先通过 `household_memberships` 校验访问权，无权访问统一返回 HTTP 404。
- 新增、编辑、设备绑定要求家庭管理员权限；普通成员可查看和执行允许的控制操作。
- 房间名称去除首尾空格后长度为 1～80；主题色只允许 `#RRGGBB`；设备 ID 必须属于同一家庭。
- 创建房间、批量控制、执行场景与生成报告接受 `Idempotency-Key`，防止网络重试造成重复写入。
- 日志中的 `detail_json` 不保存访问令牌、密码或设备密钥；导出地址使用短期签名 URL。
