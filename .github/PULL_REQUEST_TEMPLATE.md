## 改动内容

<!-- 简要说明这个 PR 做了什么、为什么需要它。关联 Issue：Closes #123 -->

## 影响范围

- [ ] 后端（`smarthome-api`）
- [ ] 前端（`smarthome-web`）
- [ ] 文档（`README.md` / 子项目 README / 代码注释）
- [ ] 构建 / 脚本 / CI

是否涉及破坏性变更？

- [ ] 否
- [ ] 是（请在下方说明迁移方式）

## 验证方式

<!-- 写明你实际执行过的命令与结果，例如 npm run test:unit、手动复现步骤 -->

```bash
# 示例
cd smarthome-api && uv sync && uv run pytest -q
cd smarthome-web && npm run type-check && npm run test:unit
```

## 自查清单

- [ ] 改动聚焦，一个 PR 只做一件事
- [ ] 提交信息符合约定式提交（如 `feat(agents): ...`）
- [ ] 已为新增逻辑补充必要注释或文档
- [ ] 涉及接口 / OpenAPI 变更时已重新生成前端类型（`npm run api:generate`）
- [ ] 未提交 `.env`、数据库、日志等运行时产物
