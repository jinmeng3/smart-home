# 登录接口与数据库设计

本文档定义前端已经预留的登录契约。当前仓库不实现登录后端；在接口完成前，登录弹窗会正常展示，提交时会显示接口返回的错误。

## 1. 登录接口

`POST /api/auth/login`

请求头：`Content-Type: application/json`

请求体：

```json
{
  "account": "zhang.xm@company.com",
  "password": "用户输入的明文密码"
}
```

- `account`：必填，邮箱或用户名，前端会去除首尾空格。
- `password`：必填。仅通过 HTTPS 传输，不得记录到日志或持久化到浏览器。

成功响应（统一响应结构）：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "name": "张晓明",
      "email": "zhang.xm@company.com",
      "avatar_url": "/uploads/avatars/1.webp"
    }
  }
}
```

失败响应建议：HTTP `400` 参数错误、`401` 账号或密码错误、`423` 账号锁定、`429` 请求过于频繁。响应示例：

```json
{
  "code": 40101,
  "message": "账号或密码错误",
  "data": null
}
```

后续请求使用 `Authorization: Bearer <access_token>`。为兼容当前开发接口，前端仍会发送 `X-User-Id`；登录后端接入完成后应删除该开发身份头及服务端默认用户逻辑。

建议同时提供：

- `POST /api/auth/refresh`：输入 `refresh_token`，输出新 token 对。
- `POST /api/auth/logout`：注销当前 refresh token/会话。
- `GET /api/auth/me`：输出当前用户基础资料与权限。

## 2. 注册接口

`POST /api/auth/register`

请求头：`Content-Type: application/json`

请求体：

```json
{
  "username": "zhangxiaoming",
  "email": "zhang.xm@company.com",
  "password": "用户输入的密码"
}
```

字段约束：

- `username`：必填，2～50 个字符，保存前去除首尾空格；建议仅允许中文、字母、数字、下划线和短横线。
- `email`：必填，转换为小写后进行唯一性校验。
- `password`：必填，至少 8 位；后端必须再次校验强度，禁止记录或保存明文。
- `confirmPassword` 只在前端用于一致性校验，不发送给后端。

注册成功建议返回 HTTP `201`，响应结构与登录接口一致。当前前端会在注册成功后直接保存 token 并进入已登录状态：

```json
{
  "code": 0,
  "message": "created",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 7200,
    "user": {
      "id": 4,
      "name": "zhangxiaoming",
      "email": "zhang.xm@company.com",
      "avatar_url": null
    }
  }
}
```

失败状态建议：

- HTTP `400`：字段格式或密码强度不符合要求。
- HTTP `409`：用户名或邮箱已经注册；建议错误码分别使用 `40901`、`40902`。
- HTTP `429`：同一 IP 注册过于频繁。

服务端处理顺序：规范化用户名和邮箱、检查唯一性、使用 Argon2id 或 bcrypt 生成密码哈希、创建用户、创建 refresh session，最后签发 token。用户创建和会话创建应在同一数据库事务中完成。

## 3. 数据库设计

### users（扩展现有表）

| 字段 | 类型 | 约束 | 用途 |
| --- | --- | --- | --- |
| id | bigint | PK | 用户 ID |
| username | varchar(50) | UNIQUE, NOT NULL | 登录名 |
| email | varchar(254) | UNIQUE, NOT NULL | 邮箱登录标识 |
| password_hash | varchar(255) | NOT NULL | Argon2id/bcrypt 哈希，禁止保存明文 |
| status | varchar(20) | NOT NULL, default `active` | active/locked/disabled |
| failed_login_count | int | NOT NULL, default 0 | 连续失败次数 |
| locked_until | datetime | NULL | 临时锁定截止时间 |
| last_login_at | datetime | NULL | 最后登录时间 |
| created_at | datetime | NOT NULL | 创建时间 |
| updated_at | datetime | NOT NULL | 更新时间 |

建议为规范化后的 `username` 和 `email` 分别建立唯一索引。如果数据库区分大小写，应增加 `username_normalized`、`email_normalized` 字段或使用函数索引，防止通过大小写重复注册。

### auth_sessions

| 字段 | 类型 | 约束 | 用途 |
| --- | --- | --- | --- |
| id | bigint | PK | 会话 ID |
| user_id | bigint | FK users.id, INDEX | 所属用户 |
| refresh_token_hash | varchar(255) | UNIQUE, NOT NULL | refresh token 哈希 |
| device_name | varchar(120) | NULL | 设备描述 |
| ip_address | varchar(45) | NULL | IPv4/IPv6 |
| user_agent | varchar(500) | NULL | 客户端标识 |
| expires_at | datetime | NOT NULL, INDEX | 过期时间 |
| revoked_at | datetime | NULL | 注销时间 |
| created_at | datetime | NOT NULL | 创建时间 |

访问 token 建议采用 15–120 分钟有效期；refresh token 仅保存哈希并支持单设备撤销。登录成功后重置失败次数，失败达到阈值时设置 `locked_until`，并对账号与 IP 同时限流。

## 4. 未登录展示规则

- 顶部与侧栏账户区域显示“访客用户 / 登录后同步个人信息”，不展示缓存姓名、邮箱和头像。
- 隐藏未读通知数量；进入设置页会拉起登录弹窗，不请求账户、家庭及模型数据。
- 聊天入口与基础页面仍可见；需要云端身份的接口若返回 `401`，后续可统一拦截并打开登录弹窗。

## 5. 模型与平台接入数据

前端模型选择调用 `GET /api/ai_model/models`，选项完全来自 `ai_models` 表，不再写死。返回字段包含 `id`、`name`、`provider`、`api_endpoint`、`parameters`、`temperature`、`max_tokens` 与 `is_active`。

选择模型调用 `POST /api/ai_model/models/{model_id}/activate`；服务端在同一事务中取消该用户其他模型的激活状态，保证聊天接口只使用一个当前模型。

平台差异参数放入 `ai_models.parameters` JSON，例如：

```json
{
  "organization": "org_xxx",
  "api_version": "2026-01-01",
  "deployment": "smart-home-chat",
  "extra_headers": { "X-Region": "cn-east" }
}
```

密钥继续放在 `api_key`，生产环境应使用 KMS/应用级加密，读取接口不得返回密钥。通用字段保留为表列便于查询，厂商特有字段放入 `parameters`，避免每接入一个平台就迁移数据库。
