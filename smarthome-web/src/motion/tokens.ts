/**
 * 动画时长与缓动 Token（毫秒为单位）。
 *
 * 业务配置统一使用毫秒表意；在调用 GSAP 时通过 `toSeconds()` 换算为秒。
 * 禁止在页面内散落新的时长常量，统一在此处维护。
 */
export const motionDuration = {
    /** 微交互：hover、active、单属性淡入 */
    fast: 140,
    /** 常规交互动画（滚动渐隐、状态切换） */
    base: 220,
    /** 较慢的容器级动画（折叠、展开） */
    slow: 320,
    /** 页面/卡片入场 */
    pageEnter: 360,
    /** 列表新增/删除/重排 */
    list: 240,
    /** 模态框入场（遮罩 + 面板统一编排） */
    modalIn: 280,
    /** 模态框退场 */
    modalOut: 200,
    /** 折叠面板宽度与内容 */
    collapse: 300,
    /** 数字补间 */
    number: 600,
    /** 不确定进度条单程周期 */
    indeterminate: 2000,
} as const;

/** 与 CSS `--motion-ease` 对齐的缓动曲线（GSAP 受支持） */
export const motionEase = {
    /** 快出慢收：cubic-bezier(0.22, 1, 0.36, 1) */
    ease: "cubic-bezier(0.22, 1, 0.36, 1)",
    /** 持续减速：cubic-bezier(0, 0, 0.2, 1) */
    easeOut: "cubic-bezier(0, 0, 0.2, 1)",
    /** 持续加速：cubic-bezier(0.4, 0, 1, 1) */
    easeIn: "cubic-bezier(0.4, 0, 1, 1)",
} as const;

/** 毫秒 → 秒（GSAP 使用秒） */
export const toSeconds = (milliseconds: number) => milliseconds / 1000;

/** 供 GSAP 使用：`toSeconds(motionDuration.base)` 的快捷入口 */
export const seconds = {
    fast: toSeconds(motionDuration.fast),
    base: toSeconds(motionDuration.base),
    slow: toSeconds(motionDuration.slow),
    pageEnter: toSeconds(motionDuration.pageEnter),
    list: toSeconds(motionDuration.list),
    collapse: toSeconds(motionDuration.collapse),
    modalIn: toSeconds(motionDuration.modalIn),
    modalOut: toSeconds(motionDuration.modalOut),
    number: toSeconds(motionDuration.number),
    indeterminate: toSeconds(motionDuration.indeterminate),
};