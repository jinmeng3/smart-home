# GSAP 动画资产与所有者清单

> 本文档对应阶段一交付物，记录 smarthome-web 现有动画资产分类、性能基线数据和试点迁移候选清单。
> 更新日期：随阶段二、阶段三试点完成同步刷新，`✅ 已迁移` 标记表示已完成 GSAP 接管。

## 1. 动画资产分类清单

### 1.1 微交互（保留 CSS）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 卡片 Hover 上浮 | `styles/animations.css` `.motion-card:hover` | CSS Transition | translateY(-1px) + 边框色 |
| 按钮 Hover/Active | `styles/animations.css` `.motion-button` | CSS Transition | translateY/scale + 背景色 |
| 图标色切换 | 多处 scoped CSS | CSS Transition | color 160ms |
| 头像缩放入场 | `styles/animations.css` `.avatar-in` | CSS Keyframes | scale 0.85→1 |
| 流式光标脉冲 | `styles/animations.css` `.streaming-cursor` | CSS Keyframes | opacity 脉冲 |
| 下拉菜单入场 | `styles/animations.css` `.dropdown-enter` | CSS Keyframes | translateY + scale |

### 1.2 页面入场（保留 CSS + 部分迁移 GSAP stagger）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 页面整体入场 | `styles/animations.css` `.page-enter` | CSS Keyframes | translateX(-16px) |
| 面板入场 | `styles/animations.css` `.page-enter-stagger` | CSS Keyframes | translateY(12px) |
| 卡片网格入场 | `useCardGridEnter` + 视图 | GSAP stagger | ✅ 已迁移：移除 nth-child 硬编码延迟，`AutomationCenter.vue`、`WholeHomeOverview.vue` 使用 |
| 聊天空状态 | `ChatWindow.vue` `.stagger-in` | CSS Keyframes + inline style delay | 3 个硬编码延迟（暂保留） |

### 1.3 列表动画（迁移 GSAP Flip）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 消息列表入场 | `styles/transitions.css` `.message-list-enter-*` | CSS Transition | ✅ 保留 CSS 入场 |
| 消息列表重排 | `ChatWindow.vue` + `useGsapFlip` | GSAP Flip | ✅ 已迁移：Vue 更新 DOM 前后捕获/播放 Flip，移除 `max-height: 1000px` |
| 消息列表退场 | `styles/transitions.css` `.message-list-leave-*` | CSS Transition + absolute | ✅ 已迁移：脱离文档流原位淡出，无固定上限 |
| 设备列表入场/退场 | `styles/transitions.css` `.recent-list-*` | CSS Transition + max-height | 暂保留（阶段四推广） |
| 建议列表入场/退场 | `styles/transitions.css` `.suggestion-list-*` | CSS Transition | 同左 |
| 步骤列表入场 | `AgentStatusPanel.vue` `.step-item-*` | CSS Transition | 独立于 TransitionGroup |

### 1.4 状态切换动画（保留 CSS + 试点迁移 GSAP）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 侧栏折叠三阶段 | `useCollapsePhase` | GSAP Timeline | ✅ 已迁移：Timeline 标签编排 fade-out/collapse，连续点击 kill+重播，无 setTimeout |
| Rail 折叠 | `BaseCollapsibleRail.vue` | GSAP Timeline + targets | ✅ 已迁移：提供 container/detail targets，移除了 CSS width 过渡避免冲突 |
| 状态交叉淡入淡出 | `styles/transitions.css` `.status-crossfade-*` | CSS Transition | 保持 |
| 展开/收起 | `styles/transitions.css` `.expand-*` | CSS Transition | max-height 动画（暂无对应 GSAP 试点） |

### 1.5 模态动画（试点迁移 GSAP Timeline）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 遮罩淡入淡出 | `BaseSmartModal.vue` | GSAP Timeline | ✅ 已迁移：单个 `<Transition :css="false">` |
| 面板缩放+位移 | `BaseSmartModal.vue` | GSAP Timeline | ✅ 已迁移：autoAlpha + y + scale 统一编排 |
| 内容分段延迟 | `BaseSmartModal.vue` `[data-modal-stagger]` | GSAP stagger | ✅ 已迁移：移除 CSS 分段延迟，GSAP stagger 0.06s |

### 1.6 滚动动画（保留 CSS 监测 + 未来评估 ScrollTrigger）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 侧栏滚动渐隐 | `useScrollFade` | rAF + ResizeObserver | 保持现有 |
| 聊天自动滚动 | `useAutoScroll` | rAF + ResizeObserver | 保持现有 |

### 1.7 常驻循环动画（保留 CSS Keyframes）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 悬浮上浮 | `styles/animations.css` `.float-y` | CSS Keyframes | infinite |
| 闪烁骨架屏 | `styles/animations.css` `.shimmer` | CSS Keyframes | infinite |
| 脉冲光环 | `styles/animations.css` `.pulse-ring` | CSS Keyframes | infinite |
| 思考点动画 | `styles/animations.css` `.thinking-dots` | CSS Keyframes | infinite |
| 不确定进度条 | `AIThinking.vue` / `styles/animations.css` `.thinking-progress` | CSS Keyframes（transform） | ✅ 已迁移：`xPercent/scaleX` 合并为 `transform: translateX() scaleX()`，移除 width/margin-left |
| 进度条环 | `AgentStatusPanel.vue` `.status-icon-pulse` | CSS Keyframes | 保持 |
| 对话粒子 | `ChatWindow.vue` `.particle` | CSS Keyframes | 保持 |

### 1.8 数字与状态动画（试点迁移 GSAP）

| 资产 | 位置 | 类型 | 说明 |
|------|------|------|------|
| 数字补间 | `useAnimatedNumber` | GSAP Tween | ✅ 已迁移：`overwrite: "auto"`，reduced 直接终值，销毁 kill |
| Agent 状态标签 | `AnimatedStatus.vue` | CSS Transition | 保持 |

## 2. 布局属性动画标记

以下动画使用了 `width`、`margin-left`、`max-height` 等布局属性，在低性能设备上可能引起 Layout 抖动。更新：试点项已迁移为 transform 方案：

| 位置 | 属性 | 状态 |
|------|------|------|
| `styles/animations.css`/`AIThinking.vue` `.thinking-progress` | ~width, margin-left~ | ✅ 已迁移：`transform: translateX()+scaleX()` |
| `styles/transitions.css` `.message-list-leave-active` | ~max-height: 1000px~ | ✅ 已迁移：`position: absolute` + Flip 接管重排 |
| `styles/transitions.css` `.expand-*` | max-height: 180px | 保留（暂无接手方案，列表量小） |
| `BaseCollapsibleRail.vue` | width | 保留（GSAP Timeline 直接补间 width 并 clearProps；容器折叠必需） |

## 3. 固定定时器编排标记

| 位置 | 定时器 | 状态 |
|------|--------|------|
| `useCollapsePhase.ts` | ~2× setTimeout~ | ✅ 已迁移：GSAP Timeline + 标签 |
| `useAnimatedNumber.ts` | ~requestAnimationFrame~ | ✅ 已迁移：GSAP Tween + overwrite:auto |
| `ChatWindow.vue` `handleRegenerate` | 1× setTimeout 180ms | 保留（退场延迟，业务意图） |
| `AgentStatusPanel.vue` | 1× setTimeout 420ms | 保留（折叠文案展示延迟） |

## 4. 减少动态效果处理不一致

下表列出了分散在各处的 `@media (prefers-reduced-motion: reduce)` 规则：

| 位置 | 处理方式 | 口径 |
|------|----------|------|
| `styles/animations.css` | 全局 * { animation-duration: 1ms } | 全局 |
| `App.vue` | aside/nav 过渡 1ms | 组件级 |
| `BaseSmartModal.vue` | 过渡/动画 1ms | 组件级 |
| `BaseCollapsibleRail.vue` | 动画/过渡 1ms | 组件级 |
| 其他 15+ 组件 | 过渡/动画 1ms 或 none | 组件级 |

**整改**：公共 `useMotionMode`（`src/motion/motionMode.ts`）已集中计算
`data-motion="off"` > 系统 `prefers-reduced-motion` / `data-performance="lite"` > full。
新迁移组件（数字、折叠、模态、卡片 stagger、Flip）均以 `isReduced` 决定是否播放动画，
未播放时直接呈现终态。组件级 CSS `1ms` 规则保留作为兜底兼容。

## 5. 性能基线

### 5.1 类型检查

```bash
npm run type-check
```

### 5.2 生产构建

```bash
npm run build
```

### 5.3 Chunk 预算

```bash
node scripts/check-chunk-budget.mjs
```

> 记录：`npm run build` 内含 type-check + build-only + check:chunk 全链路，
> 结果记录见提交说明（构建通过、GSAP core 约 70KB min+gzip 由单独 chunk 承载，
> 不影响主包预算）。

## 6. 第一批 GSAP 试点组件清单

| 序号 | 试点 | 覆盖问题类型 | 状态 | 负责文件 |
|------|------|-------------|------|----------|
| 1 | 数字补间 | 自建 rAF | ✅ 完成 | `useAnimatedNumber.ts` |
| 2 | 侧栏折叠 | 固定定时器编排 | ✅ 完成 | `useCollapsePhase.ts`, `BaseCollapsibleRail.vue` |
| 3 | 模态动画 | 多段 CSS 过渡编排 | ✅ 完成 | `BaseSmartModal.vue` |
| 4 | 聊天/设备列表 | 固定 max-height 上限 | ✅ 完成（聊天） | `useGsapFlip.ts`, `ChatWindow.vue` |
| 5 | 卡片/页面入场 | 硬编码 nth-child 延迟 | ✅ 完成 | `useCardGridEnter.ts`, `AutomationCenter.vue`, `WholeHomeOverview.vue` |
| 6 | 不确定进度条 | 布局属性动画 | ✅ 完成 | `AIThinking.vue`, `styles/animations.css` |

## 7. 阶段二基础设施清单

| 文件 | 说明 |
|------|------|
| `src/motion/tokens.ts` | 时长 Token（毫秒）+ `toSeconds()`/`seconds` + `motionEase` |
| `src/motion/motionMode.ts` | 统一 MotionMode（off > reduced > full），MutationObserver 监听 data-motion/data-performance |
| `src/motion/gsap.ts` | 共享 gsap 实例 + registerFlip/registerScrollTrigger 按需插件加载器 |
| `src/motion/index.ts` | 公共出口 |
| `src/composables/useGsapScope.ts` | 作用域 composable：预挂载排队、自动 revert、matchMedia 模式 |
| `src/composables/useReducedMotion.ts` | 兼容旧导入路径，委托 `useMotionMode` |
| `src/composables/useCardGridEnter.ts` | 卡片网格 stagger 入场（阶段三新增） |
| `src/composables/useGsapFlip.ts` | Flip 列表重排（阶段三新增） |