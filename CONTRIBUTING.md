# 贡献指南

感谢你对 Orion Smart Home 的关注！本文档说明如何搭建开发环境、提交改动以及参与协作。

## 开始之前

- 提交 Issue 前，请先搜索是否已有相同问题。
- 较大的改动（新模块、破坏性 API 变更）建议先开 Issue 讨论方案，避免白做。
- 安全相关问题请不要公开提 Issue，参见 [SECURITY.md](SECURITY.md)。

## 开发环境

### 后端

```bash
cd smarthome-api
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

不使用 uv 时，可用 `python -m venv .venv` + `pip install -r requirements.txt`。

### 前端

```bash
cd smarthome-web
npm install
npm run dev
```

### 双端联调

```bash
# Windows PowerShell
./scripts/dev.ps1

# macOS / Linux / Git Bash
./scripts/dev.sh
```

## 提交前检查

请至少保证以下命令通过：

```bash
# 后端：依赖 + 测试
cd smarthome-api && uv sync && uv run pytest -q

# 前端：类型检查 + 单元测试
cd smarthome-web && npm run type-check && npm run test:unit
```

若改动涉及 OpenAPI schema 或接口模型，请同步重新生成前端类型：

```bash
cd smarthome-web && npm run api:generate
```

## 代码风格

- **Python**：遵循 PEP 8，类型标注优先使用 `X | None`，异步代码保持显式 `await`；新增模块请补 docstring 说明职责与边界。
- **TypeScript / Vue**：使用 `<script setup lang="ts">`，组件按功能域放在 `src/components/<domain>/` 下。
- **注释**：只解释「为什么」，不重复代码字面含义。
- **文档**：涉及架构变更时，同步更新本地设计文档；`docs/` 仅在本地维护，不纳入版本库，仓库内以 README 与代码注释为准。

## 提交信息

采用约定式提交，主题使用中文描述，例如：

```
feat(agents): 支持规则层置信度热更新
fix(web): 修复审批卡片在移动端的溢出
docs(readme): 补充 uv 启动方式
```

常用类型：`feat` / `fix` / `refactor` / `docs` / `chore` / `test` / `perf`。

## Pull Request 流程

1. Fork 仓库，从 `development` 分支切出特性分支（如 `feat/funnel-hot-reload`）；
2. 保持改动聚焦，一个 PR 只做一件事；
3. 填写 PR 模板，说明改动内容、影响范围与验证方式；
4. 确保提交前检查通过，并尽量补充或更新相关文档；
5. 等待 Review，根据反馈迭代。

## 目录约定

| 路径 | 说明 |
| --- | --- |
| `smarthome-api/app/agents/` | Agent 引擎：路由、图、工具、风险、审计 |
| `smarthome-api/app/session_tree/` | 会话树存储与压缩纯逻辑 |
| `smarthome-api/app/compaction/` | 上下文压缩编排层 |
| `smarthome-web/src/` | 前端源码（api / components / stores / views） |
| `scripts/` | 本地开发脚本 |
