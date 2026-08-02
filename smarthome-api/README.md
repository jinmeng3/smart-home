# Smart Home API

启动开发服务：

```bash
uvicorn app.main:app --reload
```

登录成功后使用 `Authorization: Bearer <access_token>` 访问需要认证的接口。
