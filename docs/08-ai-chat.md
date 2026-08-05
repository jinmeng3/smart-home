# AI 模型与聊天模块 API

---

## 数据库表一览

| 表名 | 说明 | 使用接口 |
|------|------|---------|
| `ai_models` | AI 模型配置（提供商、端点、参数等） | 模型 CRUD、激活 |
| `chat_sessions` | 聊天会话 | 会话 CRUD、聊天补全 |
| `chat_messages` | 聊天消息 | 获取消息、聊天补全 |

---

## 1. AI 模型管理 (AI Model)

### 1.1 列出所有 AI 模型

- **方法**: `GET /api/ai_model/models`
- **功能**: 列出当前用户配置的全部 AI 模型
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
        "provider": "string",
        "api_endpoint": "string",
        "parameters": "object",
        "temperature": "float",
        "max_tokens": "int",
        "is_active": "bool",
        "description": "string|null",
        "created_at": "datetime",
        "updated_at": "datetime|null"
      }
    ]
  }
  ```
- **数据库**: `ai_models`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.2 获取当前启用的 AI 模型

- **方法**: `GET /api/ai_model/model`
- **功能**: 获取当前用户正在启用的 AI 模型
- **输入**: 无（需认证）
- **输出**: 单个 AI 模型对象
- **数据库**: `ai_models`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.3 创建 AI 模型配置

- **方法**: `POST /api/ai_model/model`
- **功能**: 创建 AI 模型配置
- **输入**:
  ```json
  {
    "name": "string (1-100)",
    "provider": "string (1-50)",
    "api_endpoint": "string (1-200)",
    "api_key": "string|null (可选)",
    "parameters": "object (可选, 默认 {})",
    "temperature": "float (可选, 0-2, 默认 0.7)",
    "max_tokens": "int (可选, 默认 4096)",
    "is_active": "bool (可选, 默认 true)",
    "description": "string|null (可选)"
  }
  ```
- **输出**: AI 模型对象
- **数据库**: `ai_models`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.4 激活指定模型

- **方法**: `POST /api/ai_model/models/{model_id}/activate`
- **功能**: 将指定模型设为当前启用模型
- **输入**: 路径参数 `model_id`
- **输出**: AI 模型对象
- **数据库**: `ai_models`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.5 更新当前启用模型

- **方法**: `PATCH /api/ai_model/model`
- **功能**: 更新当前启用模型的配置
- **输入**: 同创建，但所有字段可选
- **输出**: AI 模型对象
- **数据库**: `ai_models`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 1.6 删除当前启用模型

- **方法**: `DELETE /api/ai_model/model`
- **功能**: 删除当前启用的 AI 模型
- **输入**: 无（需认证）
- **输出**: `204 No Content`
- **数据库**: `ai_models`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`deleteAIModel`）

---

## 2. 聊天 (Chat)

### 2.1 列出聊天会话

- **方法**: `GET /api/chat/sessions`
- **功能**: 按更新时间列出当前用户的聊天会话
- **输入**: 无（需认证）
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      {
        "id": "int",
        "title": "string",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ]
  }
  ```
- **数据库**: `chat_sessions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.2 创建聊天会话

- **方法**: `POST /api/chat/sessions`
- **功能**: 创建一条空聊天会话
- **输入**: 无（需认证）
- **输出**: 单个会话对象
- **数据库**: `chat_sessions`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.3 获取会话消息

- **方法**: `GET /api/chat/sessions/{session_id}/messages`
- **功能**: 读取指定会话的历史消息
- **输入**: 路径参数 `session_id`
- **输出**:
  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      {
        "id": "int",
        "session_id": "int",
        "role": "user|assistant",
        "content": "string",
        "created_at": "datetime"
      }
    ]
  }
  ```
- **数据库**: `chat_messages`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.4 聊天补全

- **方法**: `POST /api/chat/completions`
- **功能**: 转发聊天请求到 AI 模型，支持普通和流式响应
- **输入**:
  ```json
  {
    "model": "string|null (可选)",
    "messages": [
      { "role": "system|user|assistant|tool", "content": "string" }
    ],
    "session_id": "int|null (可选)",
    "stream": "bool (可选, 默认 false)"
  }
  ```
- **输出** (非流式): 由 AI 模型 API 返回的完整响应
- **输出** (流式): `text/event-stream` 格式的 SSE 流
- **数据库**: `chat_sessions`, `chat_messages`
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现

### 2.5 兼容 OpenAI 格式的聊天补全

- **方法**: `POST /api/v1/chat/completions`
- **功能**: 兼容 OpenAI API 格式的聊天补全接口
- **输入/输出**: 同 `/api/chat/completions`
- **数据库**: 同上
- **实现状态**: ✅ 后端已实现 — ✅ 前端已实现（`openAICompletions`/`streamOpenAICompletions`）