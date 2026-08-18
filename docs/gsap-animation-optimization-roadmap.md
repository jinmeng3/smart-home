# GSAP 动画优化阶段文档

## 1. 文档目标

本文档用于指导 `smarthome-web` 在保留现有视觉语言的基础上，引入 GSAP 优化动画架构、交互连续性和运行性能。重点不是把所有 CSS 动画改写成 JavaScript，而是让复杂动画具备统一编排、可中断控制、组件级回收和明确的减少动态效果策略。

本方案基于 GSAP Core、Vue 生命周期、性能、Timeline、ScrollTrigger、Plugins 和 Utils 的官方实践。项目是 Vue 3 应用，不引入 React 专用的 `@gsap/react`。

## 2. 当前状态与主要问题

当前前端没有 `gsap` 依赖，动画体系主要由 CSS 和 Vue Transition 构成：

- 约 107 组 CSS `@keyframes`、344 处 `transition` 声明。
- 35 处 Vue `Transition` 或 `TransitionGroup`。
- 公共动画分布于 `styles/animations.css`、`styles/transitions.css`、动画组件和大量页面 scoped CSS。
- `useAnimatedNumber` 自行维护 `requestAnimationFrame`；`useCollapsePhase` 通过多个固定时长 `setTimeout` 驱动状态。
- 消息列表等动画依赖 `max-height` 插值，会触发布局计算，并使用固定的 1000px 上限。
- 全局、性能模式和多个组件分别处理 `prefers-reduced-motion`，存在重复和规则口径不一致。
- 页面入场使用硬编码的 `nth-child` 延迟，扩展列表时需要继续增加 CSS。
- 部分常驻进度动画修改 `width`、`margin-left` 等布局属性，不利于低性能设备。

现有实现也有应当保留的良好基础：

- 已有统一的 motion 时长和 easing CSS Token。
- `useReducedMotion`、`useAutoScroll` 和 `useScrollFade` 已考虑清理与 rAF 节流。
- 简单 hover、active、颜色过渡适合继续由 CSS 承担。
- `data-motion="off"` 和 `data-performance="lite"` 已提供用户级控制入口。

## 3. 优化原则与目标架构

### 3.1 技术边界

| 场景 | 负责技术 | 说明 |
|------|----------|------|
| hover、active、颜色和单属性淡入 | CSS Transition | 保持零运行时和即时响应 |
| 单元素简单循环状态 | CSS Keyframes | 如光标闪烁；减少动态效果下关闭 |
| 多步骤入场、状态切换和可逆交互 | GSAP Core + Timeline | 统一时间轴，支持中断、反向和清理 |
| 动态列表增删与重排 | Vue 数据流 + GSAP Flip | 由 Vue 更新 DOM，Flip 负责前后布局过渡 |
| 数字补间和高频属性更新 | GSAP Core / `quickTo()` | 代替自建 rAF 循环和重复 Tween |
| 视口触发或滚动联动 | ScrollTrigger | 仅有真实需求时按路由加载 |
| Morphicons 图标变形 | Morphicons | 不使用 MorphSVG 重复实现图标能力 |

### 3.2 Vue 生命周期约定

- GSAP 动画只在 `onMounted` 后创建。
- 每个动画组件提供根元素 `ref`，通过 `gsap.context(callback, root)` 限定选择器作用域。
- `onUnmounted` 或 `onScopeDispose` 必须调用 `context.revert()`；事件监听器和 Observer 同步移除。
- 组件外不使用无作用域的字符串选择器。
- 插件只在应用级或公共加载模块注册一次，不在组件更新路径重复注册。
- 异步数据改变 ScrollTrigger 布局后，在 Vue `nextTick` 后按需调用一次 `ScrollTrigger.refresh()`，不在滚动或每次 resize 中重复刷新。

### 3.3 动效策略

- 进入动画以 `autoAlpha`、`x`、`y`、`scale` 为主，避免用 `top`、`left`、`width`、`height` 和 margin 驱动移动。
- 多元素同类入场使用 `stagger`，不再维护 `nth-child` 延迟表。
- 多步骤动画使用 Timeline 的 position 参数和标签，不用相互叠加的 `delay` 或 `setTimeout` 编排。
- 用户连续触发时使用 `overwrite: "auto"`，避免旧 Tween 与新 Tween 竞争。
- `will-change` 只用于真正处于动画期或高频交互的节点，不全局铺设。
- 使用 `gsap.matchMedia()` 统一处理桌面、移动端、减少动态效果和性能模式；回调退出时由 GSAP 自动 revert。

## 4. 公共接口设计

新增公共 GSAP 入口和 Vue 组合式能力，页面不得各自重复初始化：

```ts
type MotionMode = "full" | "reduced" | "off";

interface MotionContext {
    gsap: typeof import("gsap").gsap;
    mode: Readonly<Ref<MotionMode>>;
    isReduced: Readonly<Ref<boolean>>;
}

interface UseGsapScopeResult {
    root: Ref<HTMLElement | null>;
    create: (setup: () => void) => void;
    revert: () => void;
}
```

实现约定：

- 公共入口导出同一个 `gsap` 实例、Motion Token 和按需插件加载器。
- `useGsapScope` 负责 mounted 后创建 scope、监听动态效果模式并在销毁时 revert。
- `MotionMode` 综合系统 `prefers-reduced-motion`、`data-motion="off"` 和 `data-performance="lite"`：显式关闭优先级最高，其次系统减少动态效果，最后是完整动画。
- 动画 Token 使用毫秒表达业务配置，在传入 GSAP 时转换为秒；禁止页面散落新的时长常量。
- ScrollTrigger、Flip 等插件通过独立具名加载函数注册；未使用的插件不进入首屏主包。

## 5. 分阶段实施

### 阶段一：建立动画基线和分类清单

#### 目标

冻结优化边界，建立可量化基线，避免将简单动画过度工程化。

#### 任务

1. 将现有动画按微交互、页面入场、列表、状态、模态、滚动、常驻循环七类登记。
2. 标记布局属性动画、固定定时器编排、重复 keyframes 和未完整处理减少动态效果的规则。
3. 记录桌面与移动端的主要交互：侧栏折叠、模态开关、聊天消息、设备列表、Agent 执行状态、数字更新。
4. 使用浏览器 Performance 面板记录动画期间的 FPS、长任务、Layout 和 Paint；选择中低端设备或 CPU 节流场景复测。
5. 建立保留 CSS、迁移 GSAP、删除重复三类清单。

#### 交付物

- 动画资产与所有者清单。
- 性能基线和视觉回归截图。
- 第一批 GSAP 试点组件清单。

#### 验收标准

- 所有迁移项都有明确原因，不以“统一技术”为唯一迁移动机。
- 试点至少覆盖时间轴、动态高度、列表和数字补间四类问题。
- 迁移前 `npm run type-check`、`npm run build` 和 chunk 预算结果已记录。

### 阶段二：建设 GSAP 基础设施

#### 目标

建立可复用、可清理、遵守用户动态偏好的 GSAP 接入层。

#### 任务

1. 增加 `gsap` 运行时依赖，不增加 `@gsap/react`。
2. 实现公共 GSAP 入口、Motion Token、`useGsapScope` 和统一 MotionMode。
3. 使用 `gsap.matchMedia()` 管理断点和减少动态效果；组件销毁时执行 `revert()`。
4. 为动态创建的事件回调提供在现有 context 内注册动画的封装，避免销毁后残留 Tween。
5. 建立插件加载约定：Flip 为近期按需能力；ScrollTrigger、ScrollToPlugin 和其他插件默认不加载。

#### 交付物

- GSAP 公共运行时模块和 Vue composable。
- 动画 Token 与减少动态效果策略。
- 面向开发者的动画使用约定。

#### 验收标准

- 同一组件多次挂载、卸载后不存在活动 Tween、Timeline 或残留内联样式。
- 多实例组件的选择器不会相互影响。
- 切换系统动态偏好或应用设置后，动画策略立即更新并清理旧状态。
- GSAP 对首屏 chunk 的增量符合现有预算。

### 阶段三：迁移高收益试点

#### 目标

优先替换维护成本高或容易产生卡顿的实现，验证公共层设计。

#### 任务

1. **数字动画**：以 GSAP 对普通对象属性补间，替换 `useAnimatedNumber` 自建 rAF；更新目标时使用 `overwrite: "auto"`，减少动态模式直接设为终值。
2. **侧栏折叠**：用可逆 Timeline 替换 `useCollapsePhase` 的多段 `setTimeout`；使用标签描述内容淡出、容器折叠和内容淡入，连续点击时从当前进度反向或继续。
3. **模态动画**：保留焦点管理和 Teleport，通过统一 Timeline 协调遮罩与面板；进入使用 `autoAlpha`、`y` 和 `scale`，离开完成后再通知 Vue 卸载。
4. **消息与设备列表**：先迁移新增、删除和重排的高频场景；Vue 完成数据更新前捕获 Flip 状态，DOM 更新后执行 `Flip.from()`，消除 `max-height: 1000px` 动画。
5. **页面/卡片入场**：将硬编码 `nth-child` 延迟改为 scoped target + `stagger`，低性能模式直接设置终态。
6. **不确定进度条**：用 `xPercent` 和 `scaleX` 替换 `width`、`margin-left` 动画，降低 Layout 开销。

#### 交付物

- GSAP 版数字、侧栏、模态和列表试点。
- 试点前后性能与交互对比记录。
- 经验证的 Timeline、Flip 和 stagger 示例。

#### 验收标准

- 侧栏在连续点击时无锁死、跳帧或定时器错序。
- 消息高度不受固定上限约束，删除和重新生成无需人为等待固定毫秒数。
- 模态退场结束、焦点恢复和 DOM 卸载顺序正确。
- 试点动画主要更新 transform 与 opacity，Performance 记录中无持续布局抖动。
- 减少动态和关闭动画模式均直接呈现可操作终态。

### 阶段四：按模块推广并清理重复 CSS

#### 目标

将验证后的模式推广到复杂页面，同时保留适合 CSS 的轻量交互。

#### 任务

1. 按聊天与 Agent、设备、房间、场景与自动化、设置的顺序迁移复杂动画。
2. 将重复页面入场、状态切换、展开收起抽取为公共 Timeline 工厂或 composable；不抽象只使用一次的业务序列。
3. 合并重复 keyframes、Transition 名称和组件级减少动态规则。
4. 删除已被 GSAP 接管的 `setTimeout` 编排、自建 rAF 和 max-height 过渡。
5. 保留按钮 hover、focus、颜色变化、简单光标闪烁等 CSS 动画。
6. 使用 `gsap.utils.toArray` 或 scoped selector 获取列表目标，使用 `clamp`、`mapRange`、`snap` 处理输入范围，避免重复数学工具函数。

#### 交付物

- 统一的复杂动画实现和缩减后的 CSS 动画文件。
- 清理后的动画组件与 composable。
- 模块级视觉回归记录。

#### 验收标准

- 不再存在依赖固定动画时长才能执行业务状态更新的逻辑。
- 组件销毁后不存在运行中的无限 Tween、Observer 或事件监听器。
- CSS Transition 与 GSAP 不同时修改同一元素的同一 transform 属性。
- 主要模块在完整、减少、关闭和低性能四种模式下均可正常操作。

### 阶段五：评估滚动与高级插件需求

#### 目标

只在真实产品需求和性能收益明确时引入插件，避免扩大初始包和维护面。

#### 任务

1. 若新增视口触发卡片动画，按路由懒加载 ScrollTrigger，并使用 `once` 或 batch 控制实例数量。
2. 若出现滚动进度联动，选择 `scrub`；若只需进入/离开播放，选择 `toggleActions`，同一 Trigger 不混用。
3. 动态内容改变触发位置时，在 `nextTick` 后合并调用 `ScrollTrigger.refresh()`。
4. 若产品需要可取消的程序化滚动，再评估 ScrollToPlugin；当前聊天粘底逻辑继续保留原生滚动。
5. 不引入 ScrollSmoother、SplitText、MorphSVG、DrawSVG、Draggable 或 Inertia，除非出现对应的明确交互需求。
6. GSDevTools 仅允许开发环境按需加载，不进入生产包。

#### 交付物

- 插件采用或不采用的决策记录。
- 如采用 ScrollTrigger，提供路由级懒加载、refresh 和清理验证。

#### 验收标准

- 未使用插件不进入生产构建。
- ScrollTrigger marker 不出现在生产环境。
- 路由切换后 ScrollTrigger 数量回到预期值，不引用已卸载节点。

## 6. 测试与验收矩阵

| 类型 | 场景 | 预期结果 |
|------|------|----------|
| 生命周期 | 重复进入和离开路由 | Tween、Timeline、插件实例和内联样式完整回收 |
| 中断控制 | 快速开关侧栏、模态和详情面板 | 从当前状态平滑反向或覆盖，无锁死 |
| 动态列表 | 消息新增、删除、重新生成、设备排序 | 布局连续，无固定高度截断 |
| 数字更新 | 数值连续快速变化 | 从当前值补间到最新值，不堆积 rAF/Tween |
| 响应式 | 桌面、平板、移动端 | 位移和 stagger 密度适配，不影响布局 |
| 动态偏好 | full、reduced、off、lite | reduced/off 直接到达终态，lite 移除高成本效果 |
| 性能 | CPU 节流下操作主要页面 | 无持续 Layout 抖动，帧率不低于迁移基线 |
| 可访问性 | 模态、导航、滚动和焦点 | 动画不改变焦点顺序，不延迟关键操作 |
| 工程质量 | 类型检查、构建、chunk 检查 | 全部通过，无未注册插件或无效导入 |

建议增加基于假定时钟的 composable 测试，验证目标更新、revert、减少动态和卸载清理；视觉动画本身以浏览器交互测试和截图回归为主，避免断言逐帧实现细节。

## 7. 性能预算

- 动画原则上只更新 transform 和 opacity；必须更新布局属性时，需要在代码审查中说明原因。
- 单个普通交互动画建议控制在 140–320ms，信息确认类动画不阻塞业务操作。
- 同屏列表入场限制可见节点数量，长列表依赖现有分页或虚拟化，不创建数百个同步 Tween。
- `will-change` 不全局设置；动画完成后由 context revert 或 `clearProps` 恢复 CSS 控制。
- 高频 pointer/scroll 输入使用 `quickTo()` 或复用函数，不在每个事件中创建新 Timeline。
- ScrollTrigger `refresh()` 只在真实布局变化后调用并进行合并，不放入滚动更新循环。

## 8. 风险与控制措施

| 风险 | 影响 | 控制措施 |
|------|------|----------|
| GSAP 与 Vue Transition 同时控制 transform | 动画跳变或最终状态错误 | 每个节点明确唯一动画所有者，分阶段移除旧规则 |
| context 清理遗漏 | 路由切换后内存泄漏或操作旧节点 | 所有组件统一通过 `useGsapScope` 创建并在销毁时 revert |
| 动画完成回调承载业务逻辑 | 用户关闭动画时业务不执行 | 业务状态先更新；动画回调只负责视觉收尾或卸载协调 |
| 插件过度引入 | 首屏包变大、维护复杂 | 插件按需懒加载，首期只引入 GSAP Core |
| Flip 测量大量节点 | 长列表出现同步布局成本 | 只捕获可见或变化节点，长列表保持分页/虚拟化 |
| 减少动态策略冲突 | 用户设置与系统偏好表现不一致 | 集中计算 MotionMode，删除组件散落的重复判断 |
| 全量迁移造成视觉回归 | 多页面同时失稳 | 先试点再逐模块推广，每阶段可独立回滚 |

## 9. 提交与回滚策略

各阶段独立提交：基础设施不改变现有视觉；试点一次只迁移一种动画模式；模块推广不夹带布局、颜色或业务重构。旧 CSS 仅在对应 GSAP 实现完成验收后删除。

发生回归时优先回滚当前组件到既有 CSS/Vue Transition，不回滚公共 MotionMode。GSAP 的引入不改变 API、Store、路由和后端协议，因此回滚范围保持在前端表现层。

## 10. 完成定义

满足以下条件后，动画优化视为完成：

1. 复杂动画通过统一 GSAP Vue 接入层创建、作用域化并清理。
2. 固定定时器编排、自建数字 rAF 和高频 max-height 动画已被替换。
3. 简单微交互仍由 CSS 承担，项目不存在为迁移而迁移的重复实现。
4. full、reduced、off 和 lite 四种模式行为明确且一致。
5. 类型检查、生产构建、chunk 预算、交互回归和性能基线全部通过。
6. ScrollTrigger 和其他插件只有在明确需求下按需加载，未使用能力不进入生产包。
