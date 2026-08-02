# 设备图片上传接口设计

本文档补充“添加设备/编辑设备”界面从图片地址输入改为上传图片后的后端契约。当前前端弹窗已改为文件选择和本地预览，后端实现时建议先上传图片，再把返回的 `image_url` 写入设备创建或更新接口。

## 数据库

沿用现有 SQLite 数据库 `db/orion_home.db`。

### device 表变更

现有 `device.image_url` 字段继续保留，用于保存上传后的图片访问地址。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| image_url | varchar(255) NULL | 上传成功后的设备图片地址，例如 `/uploads/devices/20260802-light.png` |

可选新增图片元数据表，便于后续清理孤立文件和做审计：

### device_image

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | integer PK autoincrement | 主键 |
| device_id | integer NULL | 关联 `device.id`，创建设备前上传时可为空 |
| original_name | varchar(255) NOT NULL | 用户上传的原始文件名 |
| storage_name | varchar(255) NOT NULL | 服务端保存文件名 |
| image_url | varchar(255) NOT NULL | 前端可访问地址 |
| mime_type | varchar(64) NOT NULL | `image/png`、`image/jpeg`、`image/webp` |
| size_bytes | integer NOT NULL | 文件大小 |
| created_at | datetime NOT NULL | 上传时间 |

## 上传设备图片

`POST /api/devices/images`

Content-Type：`multipart/form-data`

输入：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | File | 是 | 图片文件，支持 PNG、JPG、WEBP |
| device_id | integer | 否 | 编辑已有设备时可传设备主键 |

约束：

- 最大文件大小建议 5MB。
- 后端必须校验 MIME 类型和文件扩展名。
- 文件名由后端重新生成，不能直接信任用户文件名。
- 建议保存到后端静态目录 `/uploads/devices/`。

输出：

```json
{
  "code": 0,
  "message": "uploaded",
  "data": {
    "image_url": "/uploads/devices/20260802-183000-light.webp",
    "original_name": "light.webp",
    "mime_type": "image/webp",
    "size_bytes": 245760
  }
}
```

数据库写入：

- 如实现 `device_image` 表，写入一条图片上传记录。
- 如果传入 `device_id`，可同时更新 `device.image_url`。
- 如果未传 `device_id`，只返回 `image_url`，由创建设备接口写入 `device.image_url`。

## 创建设备时携带上传结果

`POST /api/devices`

输入仍为 JSON，其中 `image_url` 来自上传接口输出：

```json
{
  "name": "客厅灯带",
  "room": "客厅",
  "type": "light",
  "brand": "Orion",
  "connection": "Matter",
  "device_id": "matter-light-living-room",
  "firmware": "1.0.3",
  "image_url": "/uploads/devices/20260802-183000-light.webp"
}
```

输出：创建后的设备详情。

## 更新设备图片

推荐流程：

1. 前端调用 `POST /api/devices/images` 上传新图片，并传入 `device_id`。
2. 后端返回 `image_url`。
3. 前端调用 `PUT /api/devices/{id}`，把 `image_url` 写入设备资料。

`PUT /api/devices/{id}` 输入示例：

```json
{
  "image_url": "/uploads/devices/20260802-184200-camera.webp"
}
```

输出：更新后的设备详情。

## 错误输出

```json
{
  "code": 40000,
  "message": "仅支持 PNG、JPG、WEBP 图片",
  "data": null
}
```

常见错误：

| HTTP 状态码 | code | 场景 |
| --- | --- | --- |
| 400 | 40000 | 文件为空、格式不支持、文件过大 |
| 404 | 40400 | 传入的 `device_id` 不存在 |
| 500 | 50000 | 文件保存失败或数据库写入失败 |
