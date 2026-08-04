# 认证与账户模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `users` | 用户账号信息（姓名、邮箱、头像等） | 登录、注册、资料管理 |
| `auth_sessions` | 认证会话记录 | 登录、注册 |

---

## 1. 认证 (Auth)

### 1.1 登录

- **方法**: `POST /api/auth/login`
- **功能**: 验证账号密码并签发访问令牌
- **输入**:
  ```json
  {
    "account": "string (1-255)",
    "password": "string (1-128)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "access_token": "string",
      "token_type": "string",
      "expires_in": "int",
      "user": {
        "id": "int",
        "name": "string",
        "email": "string",
        "avatar_url": "string|null",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    }
  }
  ```
- **数据库**: `users`, `auth_sessions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.2 注册

- **方法**: `POST /api/auth/register`
- **功能**: 创建用户账号并返回首次登录凭证
- **输入**:
  ```json
  {
    "username": "string (2-50)",
    "email": "email",
    "password": "string (6-128)"
  }
  ```
- **输出**: 同登录响应
- **数据库**: `users`, `auth_sessions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.3 登出

- **方法**: `POST /api/auth/logout`
- **功能**: 结束客户端登录状态（JWT 由客户端清除）
- **输入**: 无（需认证）
- **输出**:
  ```json
  { "code": 0, "message": "logged out", "data": null }
  ```
- **数据库**: 不涉及
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

---

## 2. 账户 (Account)

### 2.1 获取当前用户资料

- **方法**: `GET /api/account/me`
- **功能**: 获取当前登录用户的个人资料
- **输入**: 无（需认证）
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "int",
      "name": "string",
      "email": "string",
      "avatar_url": "string|null",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```
- **数据库**: `users`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.2 更新用户资料

- **方法**: `PATCH /api/account/me`
- **功能**: 更新当前用户的姓名和邮箱
- **输入**:
  ```json
  {
    "name": "string (2-50, 可选)",
    "email": "email (可选)"
  }
  ```
- **输出**: 同获取用户资料
- **数据库**: `users`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.3 上传头像

- **方法**: `POST /api/account/me/avatar`
- **功能**: 上传当前用户头像，返回新的头像访问地址
- **输入**: `multipart/form-data`，字段名 `avatar`，文件类型
- **输出**:
  ```json
  {
    "code": 0,
    "message": "created",
    "data": { "avatar_url": "string" }
  }
  ```
- **数据库**: `users`（更新 `avatar_url` 字段）
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.4 删除头像

- **方法**: `DELETE /api/account/me/avatar`
- **功能**: 删除当前用户头像，清空账号中的头像地址
- **输入**: 无（需认证）
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": { "avatar_url": null }
  }
  ```
- **数据库**: `users`（清空 `avatar_url` 字段）
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现