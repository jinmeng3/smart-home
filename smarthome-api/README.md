# Smart Home API

基于 FastAPI、Pydantic 2 和 SQLAlchemy 2 构建的 Orion 智能家居后端。

## 环境配置

在 `smarthome-api` 目录创建 `.env`，至少配置安全的 JWT 密钥：

```dotenv
JWT_SECRET_KEY=replace-with-a-long-random-secret
```

可选配置包括 `DATABASE_URL`、`DEVELOPMENT_MODE`、`CORS_ORIGINS` 和
`UPLOAD_DIR`。开发模式会在启动时写入演示账号和家庭数据。

## 安装与启动

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/uvicorn app.main:app --reload
```

Linux 或 macOS 请使用 `.venv/bin/` 下的对应命令。

登录成功后使用 `Authorization: Bearer <access_token>` 访问需要认证的接口。

启动后可访问 `/docs` 查看 OpenAPI 接口文档。业务接口统一位于 `/api` 下；
兼容 OpenAI 格式的聊天入口同时提供 `/v1/chat/completions`。
