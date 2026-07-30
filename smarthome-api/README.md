# Smart Home API

启动开发服务：

```bash
uvicorn app.main:app --reload
```

开发模式使用 `X-User-Id` 请求头识别当前用户，不能用于生产环境。
