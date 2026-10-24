# smarthome-web

Orion Smart Home 的前端单页应用，基于 **Vue 3 + Vite + TypeScript**，通过 SSE 与后端 Agent 实时通信。

## 技术栈

- Vue 3（Composition API + `<script setup>`）、Vue Router、Pinia
- Vite、TypeScript、vue-tsc
- Element Plus、Tailwind CSS、GSAP
- markdown-it（消息渲染）

## 常用命令

```bash
npm install          # 安装依赖
npm run dev          # 开发服务器（默认 5173，代理 /api 与 /uploads 到后端 8000）
npm run type-check   # vue-tsc 类型检查
npm run test:unit    # 单元测试（零依赖自研 runner）
npm run build        # 类型检查 + 生产构建 + chunk 体积预算检查
npm run preview      # 预览生产构建
npm run api:generate # 从后端 OpenAPI 生成前端类型
npm run api:check    # 校验前端类型与后端 OpenAPI 是否一致
```

## 目录结构

```
src/
├── api/          # API 调用层（含 SSE 流式解析、生成的 OpenAPI 类型）
├── components/   # 通用组件（chat / device / automation / scenes / account）
├── composables/  # 组合式函数
├── stores/       # Pinia 状态管理
├── types/        # TypeScript 类型定义
├── views/        # 页面视图
├── router/       # 路由配置
└── styles/       # 全局样式
```

## 与后端联调

开发环境下 Vite 已将 `/api`、`/uploads` 代理到 `http://127.0.0.1:8000`，请先启动 `smarthome-api`。

若后端 OpenAPI schema 发生变化，重新生成类型后再提交：

```bash
npm run api:generate
```

## 环境要求

Node.js `^22.18.0 || >=24.12.0`。
