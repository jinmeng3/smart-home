# 后端开发指南

本文说明 `smarthome-api` 当前实现的运行方式和公共约定。具体业务字段与示例请继续查阅各模块文档或运行时 OpenAPI。

## 1. 技术栈与目录

- FastAPI：HTTP 路由、依赖注入、OpenAPI 与 SSE 响应。
- SQLAlchemy 2：ORM、事务和数据库连接。
- Pydantic Settings：从 `.env` 和环境变量加载配置。
- PyJWT + bcrypt：访问令牌和密码哈希。
- SQLite：默认数据库；连接启用外键、WAL 和 30 秒 busy timeout。

```text
smarthome-api/
├─ app/main.py             # 应用创建、异常处理、CORS、静态文件和启动初始化
├─ app/api/router.py       # /api 路由注册入口
├─ app/api/routes/         # 各业务领域的 HTTP 接口
├─ app/api/deps.py         # 数据库、认证、家庭成员与管理员依赖
├─ app/schemas/            # Pydantic 请求/响应模型
├─ app/models/             # SQLAlchemy 数据模型
├─ app/services/           # 业务逻辑与外部模型调用
├─ app/db/                 # Engine、Session 和建表逻辑
└─ app/uploads/            # 默认上传目录
```

路由只负责校验、授权和编排；可复用业务逻辑优先放在 `services` 中。

## 2. 本地启动

要求 Python 3.10 或更高版本。以下命令在 `smarthome-api` 目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Linux 或 macOS 激活环境时使用 `source .venv/bin/activate`。启动后可访问：

- API：`http://127.0.0.1:8000/api`
- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`
- 上传文件：`http://127.0.0.1:8000/uploads/...`

首次启动会自动创建数据库目录、上传目录和缺失的数据表。

## 3. 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `JWT_SECRET_KEY` | 是 | 无 | HS256 签名密钥；生产环境必须使用高强度随机值。 |
| `APP_NAME` | 否 | `Smart Home API` | OpenAPI 中的应用名称。 |
| `DEVELOPMENT_MODE` | 否 | `true` | 当前作为运行环境标记。 |
| `DATABASE_URL` | 否 | `sqlite:///./db/orion_home.db` | SQLAlchemy 数据库 URL。 |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | 否 | `3600` | 访问令牌有效期。 |
| `MAX_FAILED_LOGIN_ATTEMPTS` | 否 | `5` | 触发临时锁定前的失败次数。 |
| `LOGIN_LOCK_SECONDS` | 否 | `900` | 登录锁定时间。 |
| `CORS_ORIGINS` | 否 | 本地 Vite 地址 | JSON 数组格式的允许来源。 |
| `UPLOAD_DIR` | 否 | `app/uploads` | 上传文件根目录。 |
| `MAX_AVATAR_SIZE` | 否 | `2097152` | 头像最大字节数。 |
| `ALLOWED_AVATAR_TYPES` | 否 | JPEG/PNG/WebP | JSON 数组格式的头像 MIME 白名单。 |
| `MAX_DEVICE_IMAGE_SIZE` | 否 | `5242880` | 设备图片最大字节数。 |
| `ALLOWED_DEVICE_IMAGE_TYPES` | 否 | JPEG/PNG/WebP | JSON 数组格式的设备图片 MIME 白名单。 |

配置相对路径以启动命令的当前工作目录为基准，因此应从 `smarthome-api` 目录启动服务。

## 4. 认证与授权

登录或注册成功后返回 HS256 JWT。受保护接口要求：

```http
Authorization: Bearer <access_token>
```

令牌包含 `user_id`、`type=access`、签发时间和过期时间。后端目前不保存令牌会话或撤销列表，因此 `/api/auth/logout` 只用于结束客户端状态，客户端仍需删除本地令牌。

家庭资源采用两级授权：家庭成员必须存在对应 `household_memberships` 记录；管理员操作还要求角色为 `admin`。成员管理会阻止删除自己、修改自己的角色，以及删除或降级家庭最后一名管理员。

## 5. 请求与响应协议

大多数 JSON 接口使用统一包装：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

创建接口通常返回 HTTP `201` 和 `message: "created"`；部分删除接口返回 HTTP `204`，没有响应体。聊天补全是例外：它保持模型服务/OpenAI 风格响应，不套用 `ApiResponse`。

| HTTP | 业务码 | 含义 |
|-----:|-------:|------|
| 400 | 40000 | 请求或业务规则不成立 |
| 401 | 40100 | 未认证、令牌无效或过期 |
| 403 | 40300 | 没有资源权限 |
| 404 | 40400 | 资源不存在 |
| 409 | 40900 | 唯一性或状态冲突 |
| 413 | 41300 | 上传内容过大 |
| 415 | 41500 | 不支持的媒体类型 |
| 422 | 42200 | 参数校验失败 |
| 423 | 42300 | 登录尝试过多导致账号临时锁定 |
| 429 | 42900 | 请求过于频繁 |
| 500 | 50000 | 未处理的服务端错误 |
| 502 | 50200 | 上游模型或服务错误 |

参数校验失败时，`data.errors` 包含 `field`、`message` 和 `type`。服务端未知异常只向客户端返回通用消息，完整堆栈写入服务端日志。

## 6. 字段命名与时间

- 账户、设备和部分 AI 接口主要使用 `snake_case`。
- 房间、场景、自动化、总览及用户偏好中的部分 Schema 通过 Pydantic alias 输出 `camelCase`。
- 客户端不要自行猜测命名，应以对应模块示例或 OpenAPI Schema 为准。
- 时间字段由 Pydantic 序列化为 ISO 8601 字符串；家庭时区使用 IANA 名称，例如 `Asia/Shanghai`。

## 7. 数据库与文件

- 默认数据库文件为 `smarthome-api/db/orion_home.db`。
- 请求结束后数据库 Session 自动关闭；写操作由服务或路由显式提交与回滚。
- SQLite 连接启用外键约束、WAL 和 30 秒 busy timeout。
- 应用启动仅调用 `Base.metadata.create_all()`，适合创建缺失表，但不会迁移已有表结构。
- 头像保存在 `<UPLOAD_DIR>/avatars`，设备图片保存在 `<UPLOAD_DIR>/devices`，并通过 `/uploads` 提供访问。

生产环境变更表结构时应使用版本化迁移流程，不应依赖 `create_all()` 修改现有列。

## 8. 聊天与流式响应

聊天补全提供 `POST /api/chat/completions` 和兼容入口 `POST /api/v1/chat/completions`。两者都需要 Bearer Token。

`stream=false` 时返回普通 JSON；`stream=true` 时返回 `text/event-stream`。请求消息会保存到聊天会话，模型回复在完成后写入 `chat_messages`。调用前必须为当前用户配置并启用一个 AI 模型。

## 9. 验证与类型同步

安装依赖后可执行 `python -m pytest`。当前仓库未提供独立的后端测试目录，因此该命令主要作为未来测试入口。

前端 OpenAPI 类型同步流程：

```powershell
cd ..\smarthome-web
npm run api:generate
npm run api:check
```

执行前必须安装后端依赖并配置 `JWT_SECRET_KEY`。

## 10. 生产部署注意事项

- 替换示例 JWT 密钥，关闭不需要的开发配置，并只允许实际前端域名跨域。
- 将数据库和上传目录放在持久化存储上，并设置备份策略。
- 由反向代理终止 TLS，并限制请求体大小和访问频率。
- 多实例部署时不要继续依赖本地 SQLite 与本地上传目录。
- 当前登出不会服务端撤销 JWT；如需即时失效，应增加令牌版本或撤销表。
- 对 AI 模型密钥、访问日志及家庭设备操作日志执行脱敏和最小权限控制。
