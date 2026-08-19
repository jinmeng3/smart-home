import { getCurrentScope, onScopeDispose, ref, type Ref } from "vue";
import { gsap, motionEase, seconds, useMotionMode } from "../motion";

/**
 * 侧栏折叠三阶段动画状态机（GSAP 时间轴版本）。
 *
 * 收起：expanded → collapsing（内容淡出）→ collapsed（容器折叠）
 * 展开：collapsed → expanding（容器展开）→ expanded（内容淡入）
 *
 * `collapsed` 控制实际布局，`phase` 描述当前动画阶段，供外部类名/状态消费。
 *
 * - 提供 `options.targets` 时使用单条 paused GSAP 时间轴编排动画，连续点击
 *   通过 play/reverse 响应，从当前进度反向播放，不再 kill 重建。
 * - 未提供 targets（如在 Pinia store 中使用）或无 DOM 目标时，直接切换
 *   终态，不创建定时器。
 * - 减少动态效果模式下始终直接切换终态。
 */
export type CollapsePhase = "expanded" | "collapsing" | "collapsed" | "expanding";

export interface CollapseTargets {
    /** 折叠容器（宽度动画目标） */
    container: HTMLElement | null;
    /** 内容区元素（淡出/淡入目标），可为多个 */
    detail?: HTMLElement | HTMLElement[] | null;
    /** 折叠后的宽度（未提供时读取 CSS 变量 `--rail-width-collapsed`，默认 46） */
    collapsedWidth?: number;
    /** 展开后的宽度（未提供时读取 CSS 变量 `--rail-width-expanded`，默认 330） */
    expandedWidth?: number;
}

interface UseCollapsePhaseOptions {
    /** 获取当前动画目标元素（需在 mounted 后返回有效 DOM） */
    targets?: () => CollapseTargets | null;
}

const toArray = (value: HTMLElement | HTMLElement[] | null | undefined) =>
    value == null
        ? []
        : Array.isArray(value)
          ? value
          : [value];

export const useCollapsePhase = (
    initialCollapsed: boolean,
    onCollapsedChange?: (collapsed: boolean) => void,
    options: UseCollapsePhaseOptions = {},
) => {
    const { isReduced } = useMotionMode();
    const collapsed = ref(initialCollapsed);
    const phase = ref<CollapsePhase>(initialCollapsed ? "collapsed" : "expanded");
    const animating = ref(false);
    /** 单条 paused Timeline，通过 play/reverse 响应连续点击 */
    let timeline: gsap.core.Timeline | null = null;
    /** 当前 Timeline 关联的容器元素，用于判断是否需要重建 */
    let timelineContainer: HTMLElement | null = null;
    /** 上次创建时间线时的 detail 元素快照，用于检测 DOM 结构变化 */
    let lastDetailEls: HTMLElement[] = [];

    const setCollapsed = (value: boolean) => {
        if (collapsed.value === value) return;
        collapsed.value = value;
        onCollapsedChange?.(value);
    };

    const kill = () => {
        if (timeline) {
            timeline.kill();
            timeline = null;
        }
        timelineContainer = null;
        lastDetailEls = [];
    };

    const resolveWidths = (targets: CollapseTargets) => {
        let collapsedWidth = targets.collapsedWidth;
        let expandedWidth = targets.expandedWidth;

        if (
            targets.container &&
            (collapsedWidth === undefined || expandedWidth === undefined)
        ) {
            const style = getComputedStyle(targets.container);
            collapsedWidth ??=
                parseFloat(
                    style.getPropertyValue("--rail-width-collapsed"),
                ) || 46;
            expandedWidth ??=
                parseFloat(
                    style.getPropertyValue("--rail-width-expanded"),
                ) || 330;
        }

        return {
            collapsedWidth: collapsedWidth ?? 46,
            expandedWidth: expandedWidth ?? 330,
        };
    };

    /**
     * 创建或更新单条 paused Timeline。
     * 收起方向：内容淡出(0s) → 容器折叠(0.14s)
     * 展开方向：容器展开(0s) → 内容淡入(0.3s)
     */
    const ensureTimeline = (targets: CollapseTargets) => {
        const container = targets.container;
        if (!container) return null;

        const detail = toArray(targets.detail).filter(
            (el): el is HTMLElement => Boolean(el),
        );

        // 时间线存在、容器相同、且 detail 元素未变化时复用，
        // 保留快速连点时的中断反向播放能力。
        if (timeline && timelineContainer === container) {
            const detailChanged =
                lastDetailEls.length !== detail.length ||
                lastDetailEls.some((el, i) => el !== detail[i]);
            if (!detailChanged) {
                return timeline;
            }
        }

        // 清理旧 Timeline，重新创建以确保 detail 元素引用最新 DOM
        kill();

        lastDetailEls = detail;
        const { collapsedWidth, expandedWidth } = resolveWidths(targets);

        // 设置初始状态：展开态
        gsap.set(container, { width: expandedWidth });
        if (detail.length) {
            gsap.set(detail, { autoAlpha: 1, x: 0 });
        }

        const tl = gsap.timeline({
            paused: true,
            defaults: { ease: motionEase.ease },
            onComplete: () => {
                // 正向完成=完全收起
                gsap.set(container, { clearProps: "width" });
                setCollapsed(true);
                phase.value = "collapsed";
                animating.value = false;
            },
            onReverseComplete: () => {
                // 反向完成=完全展开
                gsap.set(container, { clearProps: "width" });
                setCollapsed(false);
                phase.value = "expanded";
                animating.value = false;
            },
        });

        // 收起方向（正向）：内容淡出 → 容器折叠
        if (detail.length) {
            tl.to(detail, { autoAlpha: 0, x: 8, duration: seconds.fast }, 0);
        }
        tl.to(container, { width: collapsedWidth, duration: seconds.collapse }, "+=0.06");

        // 如果当前处于折叠态，将时间线跳到末尾，使后续 reverse() 正确执行展开
        if (collapsed.value) {
            tl.progress(1);
        }

        timeline = tl;
        timelineContainer = container;
        return tl;
    };

    const toggle = () => {
        // 减少动态效果或没有 DOM 目标时直接切换终态
        if (isReduced.value) {
            kill();
            const next = !collapsed.value;
            phase.value = next ? "collapsed" : "expanded";
            setCollapsed(next);
            return;
        }

        const targets = options.targets?.();
        if (!targets?.container) {
            kill();
            const next = !collapsed.value;
            phase.value = next ? "collapsed" : "expanded";
            setCollapsed(next);
            return;
        }

        const tl = ensureTimeline(targets);
        if (!tl) return;

        animating.value = true;

        // 连续点击：从当前进度反向
        if (tl.isActive()) {
            tl.reverse();
            phase.value = collapsed.value ? "expanding" : "collapsing";
            return;
        }

        // 当前处于展开态（进度 0 或反向完成），正向播放收起
        if (!collapsed.value) {
            tl.play();
            phase.value = "collapsing";
            return;
        }

        // 当前处于收起态（进度 1 或正向完成），反向播放展开
        tl.reverse();
        phase.value = "expanding";
    };

    /** 首次加载不播放动画，直接设置最终状态 */
    const skipAnimation = () => {
        kill();
        phase.value = collapsed.value ? "collapsed" : "expanded";
        animating.value = false;
    };

    // 组件销毁时清理运行中的时间轴；Store 场景下无作用域则跳过
    if (getCurrentScope()) {
        onScopeDispose(kill);
    }

    return { collapsed, phase, animating, toggle, skipAnimation };
};