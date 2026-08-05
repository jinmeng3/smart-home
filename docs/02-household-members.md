# 家庭与成员模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `households` | 家庭信息（名称、地址、时区） | 家庭 CRUD |
| `household_memberships` | 家庭成员关系（角色、加入时间） | 成员管理 |
| `users` | 用户账号（关联成员信息） | 列出成员、添加成员 |

---

## 1. 家庭管理 (Household)

### 1.1 列出用户家庭列表

- **方法**: `GET /api/households`
- **功能**: 列出当前用户加入的所有家庭及成员统计
- **输入**: 无（需认证）
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      {
        "id": "int",
        "name": "string",
        "address": "string|null",
        "timezone": "string",
        "created_by": "int",
        "created_at": "datetime",
        "updated_at": "datetime",
        "role": "admin|member",
        "member_count": "int"
      }
    ]
  }
  ```
- **数据库**: `households`, `household_memberships`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.2 创建家庭

- **方法**: `POST /api/households`
- **功能**: 创建家庭，并将创建者登记为管理员
- **输入**:
  ```json
  {
    "name": "string (2-80)",
    "address": "string|null (可选, 最长255)",
    "timezone": "string (可选, 默认 Asia/Shanghai)"
  }
  ```
- **输出**:
  ```json
  {
    "code": 0,
    "message": "created",
    "data": {
      "id": "int",
      "name": "string",
      "address": "string|null",
      "timezone": "string",
      "created_by": "int",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  }
  ```
- **数据库**: `households`, `household_memberships`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`createHousehold`）

### 1.3 获取家庭详情

- **方法**: `GET /api/households/{household_id}`
- **功能**: 读取当前用户有权访问的家庭详情
- **输入**: 路径参数 `household_id`（需是该家庭会员）
- **输出**: 同创建家庭响应
- **数据库**: `households`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`getHouseholdDetail`）

### 1.4 更新家庭资料

- **方法**: `PATCH /api/households/{household_id}`
- **功能**: 更新家庭资料（仅管理员可操作）
- **输入**:
  ```json
  {
    "name": "string (可选)",
    "address": "string|null (可选, 传 null 清空)",
    "timezone": "string (可选)"
  }
  ```
- **输出**: 同创建家庭响应
- **数据库**: `households`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`updateHousehold`）

---

## 2. 家庭成员管理 (Members)

### 2.1 列出家庭成员

- **方法**: `GET /api/households/{household_id}/members`
- **功能**: 列出指定家庭的所有成员
- **输入**: 路径参数 `household_id`（需是该家庭会员）
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "items": [
        {
          "membership_id": "int",
          "user_id": "int",
          "name": "string",
          "email": "email",
          "avatar_url": "string|null",
          "role": "admin|member",
          "joined_at": "datetime"
        }
      ],
      "total": "int"
    }
  }
  ```
- **数据库**: `household_memberships`, `users`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.2 添加家庭成员

- **方法**: `POST /api/households/{household_id}/members`
- **功能**: 按邮箱将已有用户添加为家庭成员（仅管理员）
- **输入**:
  ```json
  {
    "email": "email",
    "role": "admin|member (可选, 默认 member)"
  }
  ```
- **输出**: 单个成员信息
- **数据库**: `household_memberships`, `users`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.3 修改成员角色

- **方法**: `PATCH /api/households/{household_id}/members/{membership_id}`
- **功能**: 修改家庭成员角色，确保至少保留一名管理员
- **输入**:
  ```json
  { "role": "admin|member" }
  ```
- **输出**: 单个成员信息
- **数据库**: `household_memberships`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.4 移除家庭成员

- **方法**: `DELETE /api/households/{household_id}/members/{membership_id}`
- **功能**: 移除家庭成员（不能移除自己或最后一名管理员）
- **输入**: 路径参数（需管理员权限）
- **输出**: `204 No Content`
- **数据库**: `household_memberships`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现