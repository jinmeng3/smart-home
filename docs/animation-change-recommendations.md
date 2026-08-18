# 动画增添、删除与修改建议

## 1. 文档目的

本文档基于 `smarthome-web` 当前代码，对后续动画工作给出可直接执行的增添、删除和修改建议。它补充 [GSAP 动画优化阶段文档](./gsap-animation-optimization-roadmap.md)，重点回答“具体改什么”和“优先改什么”。

项目已经引入 `gsap@3.15.0`，并完成 MotionMode、动画 Token、数字补间、卡片 stagger、Flip composable、侧栏折叠和模态框等第一批建设。因此后续工作不应重新搭建基础设施，而应先修正现有抽象，再逐步增加真正能改善操作反馈的动画。

## 2. 决策标准

每项动画变更至少满足以下一项，否则不实施：

- 帮助用户理解状态变化、空间关系或操作结果。
- 降低界面突然跳变带来的认知成本。
- 替换高成本布局动画或重复实现。
- 让动画可中断、可回收，并正确响应动态效果偏好。

以下情况默认不增加动画：

- 纯装饰且高频重复播放。
- 会延迟保存、执行、删除、导航等业务操作。
- 与已有 Morphicons、CSS hover 或 Vue Transition 重复表达同一状态。
- 只能通过长期修改 `width`、`height`、margin、padding 等布局属性实现，且没有明确必要性。

## 3. 建议总览

| 类别 | P0 | P1 | P2 |
|------|----|----|----|
| 修改 | Flip 事务 API、折叠可逆性、模态时序 | MotionMode 重建、卡片 context 回收、列表动画边界 | 滚动和高频输入优化 |
| 删除 | 重复 keyframes、完成态无限脉冲、布局型进度动画 | 旧页面延迟类、重复 reduced-motion 规则 | 无调用插件和失效动画类 |
| 增添 | 异步操作状态反馈、骨架到内容过渡 | 选中项空间连续性、列表增删反馈 | 视口动画和高级插件，仅按真实需求启用 |

P0 是正确性和动画所有权问题；P1 是一致性与性能问题；P2 只有在产品场景出现后实施。

## 4. 建议修改的动画

### 4.1 P0：重构 Flip 为数据变更事务

#### 当前问题

`useGsapFlip` 首次调用时异步加载插件，但布局状态必须同步捕获。插件尚未加载时，`capture()` 无法得到状态。当前 `captureAndFlip()` 只是连续执行捕获和 `nextTick`，没有在两者之间执行实际的数据变更；聊天窗口是在消息数量已经变化后通过 watch 调用，捕获到的已经是新布局。

#### 修改建议

将接口改为包裹数据变更的事务：

```ts
interface FlipMutationOptions {
    mutate: () => void | Promise<void>;
}

const runFlip = async (options: FlipMutationOptions): Promise<void> => {
    // 1. 确保插件已加载
    // 2. 捕获旧布局
    // 3. 执行 mutate
    // 4. await nextTick()
    // 5. Flip.from(oldState)
};
```

- 在需要 Flip 的路由或组件 mounted 后预加载插件，确保捕获阶段同步可用。
- 直接保存并调用已加载的 `Flip` 导出，删除 `(gsap as any).Flip`。
- 新动画开始前 kill 同一容器上的旧 Flip，使用 `overwrite: true` 或 `Flip.killFlipsOf()`。
- 组件销毁时清理活动 Flip，不只清空本地 state。
- 聊天流式内容变化不执行 Flip；只在消息新增、删除、重新生成和历史消息插入时执行。

#### 验收标准

- 首次列表变更也能正常动画。
- 捕获发生在 Store/数组更新之前。
- 快速连续新增或删除时没有位置跳回和重叠元素。
- reduced/off/lite 模式只执行数据更新，不测量或播放 Flip。

### 4.2 P0：让折叠 Timeline 真正可逆

#### 当前问题

`useCollapsePhase` 的说明声称连续点击会从当前进度反向或继续，但 `toggle()` 当前会先 kill Timeline，再根据布尔状态创建新 Timeline。收起过程中还会提前改变 `collapsed`，因此快速点击可能从中间视觉状态重新测量并启动，行为并不是真正可逆。

折叠过程还直接补间容器 `width`，会触发子布局变化。这在侧栏布局确有必要，但应限制影响范围并避免每次动画读取多次布局。

#### 修改建议

- 为一次组件生命周期创建一条 paused Timeline，展开与收起使用 `play()`、`reverse()` 控制。
- 以 Timeline 方向和 progress 判断目标状态，不以中途更新的 `collapsed` 推导下一次方向。
- 只在动画到达 0 或 1 时提交稳定的 `collapsed` 和 `phase` 状态。
- 尺寸在 Timeline 创建或 ResizeObserver 通知后统一读取，避免每次 toggle 重复读取 computed style。
- 若布局允许，优先用外层 grid 列宽承担布局、内层内容使用 `x`/`autoAlpha`；不要同时让 CSS `transition-[width]` 和 GSAP 修改同一宽度。

#### 验收标准

- 在动画任意进度连续点击，侧栏都能从当前位置平滑反向。
- 动画期间不存在两个宽度动画所有者。
- `phase`、`collapsed`、视觉宽度在结束后保持一致。
- 卸载、路由切换或动态模式变化时 Timeline 立即清理并落到可操作终态。

### 4.3 P0：修正模态框动画与焦点时序

#### 当前问题

`BaseSmartModal` 已用 GSAP 接管 Vue Transition，但快速开关时没有在创建新 Timeline 前 kill 旧 Timeline。入场后只对 overlay 执行 `clearProps`，panel 上的 `opacity`、`visibility`、`transform` 仍可能保留。焦点在 modelValue 变为 true 后立即移动，恢复焦点则在退场动画开始前发生，视觉与可访问时序不一致。

#### 修改建议

- `onEnter`、`onLeave` 开始时先 kill 并清空旧 `activeTimeline`，保证 Vue 的 `done()` 最终只调用一次。
- 入场完成后再聚焦对话框首个可操作元素。
- 退场完成、DOM 即将卸载后再恢复触发元素焦点。
- `onAfterEnter` 同时清理 overlay 和 panel 的 `transform,opacity,visibility`，不要使用范围过大的 `clearProps: "all"`。
- reduced/off/lite 模式调用 `done()` 后仍执行相同的焦点和 modal stack 生命周期。
- stagger 只作用于一级结构区块；长表单不对每个字段逐项延迟，避免等待感。

#### 验收标准

- 快速开关模态框不会卡住 Vue Transition。
- 入场结束后焦点位于模态框内，退场结束后回到原触发控件。
- panel 没有残留 GSAP 内联 transform 或 visibility。
- 嵌套模态框只恢复当前栈顶对应的焦点。

### 4.4 P1：让 MotionMode 能重建活动动画

#### 当前问题

`useGsapScope` 暴露 `mode` 和 `isReduced`，但已创建的动画不会自动在模式变化时重建。组件需要各自 watch，容易出现切换到 reduced 后无限动画仍运行、切回 full 后状态不一致的问题。

#### 修改建议

- 为 `useGsapScope` 增加 `createResponsive(setup)`，内部使用一个带命名 conditions 的 `gsap.matchMedia()`。
- conditions 统一包含 full、reduced、off 和移动端断点。
- 模式变化时先 revert 当前 context，再按新条件设置终态或重建动画。
- CSS 的 `data-motion="off"` 保留为兜底；JavaScript 动画以 MotionMode 为唯一决策入口。

#### 验收标准

- 动画播放中切到 off，元素立即进入稳定终态。
- 切回 full 不重复播放已经完成的业务反馈动画。
- MutationObserver、matchMedia 和 GSAP context 的连接与断开次数匹配。

### 4.5 P1：控制卡片入场 context 数量

#### 当前问题

`useCardGridEnter` 每次 `play()` 都创建并保存一个新 context，完成后仅清理内联样式，context 会保留到组件卸载。频繁分页或动态追加卡片时，数组会持续增长。

#### 修改建议

- 每次 play 只保存当前 Tween；开始新批次前仅清理已结束实例，或将新 Tween 注册到一个组件级 context。
- Tween 完成后 kill 自身并从追踪集合移除。
- `WeakSet` 只在 Tween 成功创建后登记元素，取消或异常时允许重试。
- stagger 设置最大总时长；列表较长时使用 `{ amount, from: "start" }`，避免每项固定 80ms 导致尾项等待过久。

#### 验收标准

- 连续分页后 context/Tween 数量不会线性增长。
- 20 个以上卡片的总入场时间仍在可接受范围内。
- hover transform 在入场完成后继续由 CSS 正常控制。

### 4.6 P1：统一动画 Token 与所有权

#### 当前问题

现有 GSAP 和 CSS 中仍有 `0.24`、`0.06`、`1.2s` 等局部时长，部分组件同时保留 CSS transform transition 与 GSAP transform。Token 已存在，但尚未成为强约束。

#### 修改建议

- 所有共享时长从 `motionDuration`/`seconds` 获取；只有业务特有且不复用的节奏允许局部常量，并写明原因。
- 建立节点级所有权规则：同一状态下，CSS 和 GSAP 不同时修改同一元素的 transform、opacity 或 visibility。
- CSS Token 和 TypeScript Token 保持一张来源表；短期可人工同步，后续再评估生成机制。
- 在代码审查清单中增加“动画所有者、清理、reduced、Token”四项。

## 5. 建议删除的动画

### 5.1 P0：删除重复 keyframes 定义

当前存在多处同名或同语义实现：

| 动画 | 当前情况 | 建议 |
|------|----------|------|
| `actions-fade-in` | 全局、聊天消息、房间详情重复 | 保留一个公共实现，局部文件删除 |
| `result-pulse` | Mode、Inspection、Sync 对话框分别定义 | 改为共享的一次性结果反馈，删除三个无限版本 |
| `progress-indeterminate` | 全局和 AIThinking 重复 | 保留一个 transform 版本 |
| `card-enter` | 多处重复 | GSAP stagger 覆盖的页面删除，纯 CSS 场景只保留公共版本 |
| `scene-card-enter`、`scene-spin` | 各有重复定义 | 合并到场景模块共享样式或公共动画文件 |
| `skeleton-pulse`、`step-in` | 各有重复定义 | 保留单一语义版本，统一 reduced 行为 |

删除前需确认局部版本是否存在不同关键帧；如果曲线不同，应重命名为明确业务语义，而不是继续复用同名。

### 5.2 P0：删除完成态无限脉冲

`result-pulse` 当前在多个操作结果对话框中无限播放。成功或失败是已经确定的结果，不应持续吸引注意力。

建议改为一次 240–360ms 的 `scale: 0.94 → 1` 与 `autoAlpha` 入场，必要时配合 Morphicons 的状态图标变形。完成后保持静态，不 repeat、不 yoyo。

持续脉冲只保留给真正“仍在执行”或“需要立即关注”的状态，并设置最长生命周期。

### 5.3 P0：删除布局型不确定进度动画

删除通过 `width` 和 `margin-left` 循环变化的 `progress-indeterminate`、`sync-progress-indeterminate` 和 `batch-delete-progress-indeterminate` 实现。

统一改为固定宽度轨道内的指示条：

- 指示条宽度由 CSS 固定。
- GSAP/CSS 只补间 `xPercent` 和 `scaleX`。
- reduced/off/lite 模式显示静态进度条或普通 loading 文案。
- 任务有真实进度时直接显示确定进度，不使用伪进度循环。

### 5.4 P1：删除旧的页面延迟类

`.page-enter-stagger` 实际应用在独立卡片和布局节点上，依靠组件各自挂载时间形成近似 stagger，节奏不可控。已有 `useCardGridEnter` 后，应逐页迁移并删除此类。

`.page-enter` 可以作为简单路由入场保留，但应避免一个页面的多个嵌套容器同时播放，造成整体漂移感。每个路由最多保留一个页面级入场所有者。

### 5.5 P1：删除重复的 reduced-motion 局部规则

全局已经通过 MotionMode、`data-motion`、`data-performance` 和 `prefers-reduced-motion` 提供兜底。组件中的局部规则应分类处理：

- 删除只重复设置 `animation-duration: 1ms`、`transition-duration: 1ms` 的规则。
- 保留用于取消 hover transform、停止特定无限动画或设置稳定终态的业务规则。
- 不使用 `!important` 与 GSAP 争夺同一属性；JavaScript 动画通过 MotionMode 停止，CSS 规则只管理 CSS 动画。

### 5.6 P2：删除无调用或无效果的动画基础设施

- Flip 事务 API 修正后，删除旧 `capture()`、`flip()`、`captureAndFlip()` 兼容接口。
- 若 ScrollTrigger 仍没有实际调用，保留按需加载函数可以接受，但不要提前添加插件样式、marker 或初始化代码。
- 清理模板中已没有对应 Transition 的 enter/leave 类，以及不再被引用的 keyframes。
- 使用静态扫描维护“keyframe 定义必须有引用、Transition name 必须有样式或 JS hook”的约束。

## 6. 建议增添的动画

### 6.1 P0：统一异步操作状态反馈

#### 适用场景

- 设备开关与同步。
- 场景执行。
- 自动化启停、复制、运行和批量操作。
- 设置保存与模型连接测试。

#### 建议行为

构建共享的“idle → pending → success/error”状态动画：

- pending：图标 Morph 到 loading 状态，或轻量旋转；按钮尺寸不改变。
- success：图标 Morph 到 check，并进行一次轻微 scale 强调。
- error：图标 Morph 到 warning，配合一次短促的水平位移；不持续摇晃。
- 状态文本用 `autoAlpha` 和 4px 以内 y 位移交叉淡入。
- 动画不决定 Promise 和业务状态，只消费现有状态。

同一模式应封装为公共状态反馈组件，避免每个对话框各自定义 `result-pulse`。

### 6.2 P0：增加骨架屏到真实内容的过渡

当前页面已有 skeleton 和数据加载逻辑，但内容就绪时容易瞬间替换。建议增加一次 160–220ms 交叉淡入：

- skeleton 只降低 `autoAlpha`，不先收缩高度。
- 真实内容在同一占位区域淡入，避免布局跳变。
- 首次加载使用；轮询和后台刷新不重复让整个页面入场。
- reduced/off/lite 模式直接替换。

### 6.3 P1：增加选中项到详情面板的空间连续性

设备、房间、场景和自动化均存在“卡片/列表项 → 详情区”的导航关系。建议只对图标、标题或选中背景增加轻量连续过渡，而不是让整张卡飞入面板。

- 同容器重排使用 Flip。
- 跨容器只共享少量识别元素，持续 220–320ms。
- 详情内容仍用短交叉淡入，避免大量文字缩放变形。
- 移动端侧滑详情优先表达方向；桌面端优先表达选中关系。

### 6.4 P1：增加列表操作的局部反馈

- 新增：新项从 8px y 位移与 0 autoAlpha 进入，并短暂突出边框。
- 删除：先淡出目标项，再由 Flip 重排剩余项；业务删除失败时恢复项目并显示错误状态。
- 复制：新副本从原项附近进入并自动聚焦或高亮一次。
- 批量更新：只对发生变化的可见项播放，不让整个列表重新入场。

聊天流式 token、设备实时数值等高频内容不逐次执行布局动画。

### 6.5 P1：增加导航和筛选结果的方向提示

- 侧栏组展开/收起复用真正可逆 Timeline。
- 搜索或筛选切换后，列表使用短交叉淡入或 Flip，不重复播放页面入场。
- 前进到详情和返回列表使用一致的 x 方向；不要同时叠加 scale、旋转和大幅位移。
- 仅在用户主动导航时播放，路由恢复或浏览器后退可根据历史方向选择反向或直接呈现。

### 6.6 P2：按需增加 ScrollTrigger

当前项目是应用型控制台，不需要营销页面式的滚动表演。只有出现以下场景时才增加 ScrollTrigger：

- 长报告中的章节进入提示。
- 大量卡片只在首次进入视口时播放一次。
- 滚动位置需要同步目录高亮。

使用 `once` 或 batch，路由卸载时由 scoped context 清理。不要增加 pin、横向假滚动、ScrollSmoother 或视差，除非产品明确需要。

## 7. 模块级建议

| 模块 | 增添 | 删除 | 修改 |
|------|------|------|------|
| 全局布局 | 路由级单一方向提示 | 嵌套 page-enter、page-enter-stagger | 侧栏真正可逆，CSS/GSAP 宽度所有权唯一 |
| 模态框 | 区块级轻 stagger | 重复对话框结果 pulse | 快速开关、焦点和 clearProps 时序 |
| 聊天 | 消息增删 Flip、停止/完成反馈 | 流式 token 的布局动画 | Flip 捕获必须包住 Store 变更 |
| Agent | pending → success/error 状态序列 | 完成态无限动画 | 无限动画随状态离开及时 kill |
| 设备 | 切换、同步、复制的局部反馈 | 布局型同步进度 | 批量变化只动画可见项 |
| 房间 | 选中卡片到详情的轻连续性 | 重复 actions-fade-in | 折叠与详情切换使用共享模式 |
| 场景/自动化 | 执行结果、启停和复制反馈 | 重复 scene/result keyframes | 列表新增删除使用事务 Flip |
| 设置 | 保存状态和连接测试反馈 | 保存后持续脉冲 | 表单错误只播放一次短反馈 |

## 8. 推荐实施顺序

### 第一批：正确性修复

1. 重构 Flip 事务 API，并修复聊天、设备调用点。
2. 修正侧栏可逆 Timeline。
3. 修正模态框 Timeline、焦点和内联样式清理。
4. 建立快速连续操作和卸载清理测试。

### 第二批：删除重复和高成本实现

1. 合并重复 keyframes。
2. 将完成态 pulse 改为一次性反馈。
3. 将不确定进度改为 transform 实现。
4. 删除已被 GSAP 接管的旧 Transition 和局部 reduced 规则。

### 第三批：增加高价值反馈

1. 建立公共异步状态反馈组件。
2. 接入设备、场景、自动化和设置操作。
3. 增加骨架到内容、列表增删和选中到详情的连续过渡。
4. 完成模块级视觉与性能回归。

### 第四批：按需求扩展

只有出现明确的长页面或滚动联动需求后，才评估 ScrollTrigger 和其他插件。Morphicons 继续负责图标路径变形，不引入 MorphSVG 重复实现。

## 9. 测试与完成标准

### 自动检查

- `npm run type-check`、`npm run build` 和 chunk 预算通过。
- 重复 keyframe 名称扫描结果为零，或每个重名都有明确作用域说明。
- 不存在无引用 keyframe、失配 Transition name 和生产环境 marker。
- 组件卸载后没有活动 Tween、Timeline、Flip 或全局事件监听器。

### 交互测试

- 连续快速开关侧栏、模态和详情面板 10 次，状态始终一致。
- 连续新增、删除、复制列表项，项目不重叠、不跳回。
- 动画中切换 full、reduced、off 和 lite，界面立即到达可操作终态。
- 异步操作成功、失败和取消都具有清晰但不过度的反馈。
- 键盘焦点、屏幕阅读顺序和点击区域不因动画改变。

### 性能测试

- 主要动画以 transform 和 opacity 为主。
- 不确定进度动画不产生持续 Layout。
- 中低端设备或 CPU 节流下，侧栏、模态和列表操作无明显卡顿。
- 长列表只动画可见或变化项目，动画实例数不会随历史操作持续增长。

## 10. 明确不建议的改动

- 不把所有 CSS hover 和颜色 Transition 改成 GSAP。
- 不给每张卡片增加永久漂浮、呼吸或视差效果。
- 不在操作成功后持续播放 pulse、bounce 或 glow。
- 不以动画完成回调作为保存、删除和执行请求的必要条件。
- 不同时用 Morphicons 和 MorphSVG 控制同一个图标。
- 不为控制台页面引入全局平滑滚动或滚动劫持。
- 不为了展示技术能力而引入未被产品场景使用的 GSAP 插件。
