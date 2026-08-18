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
 * - 提供 `options.targets` 时使用可逆 GSAP 时间轴编排动画，连续点击会
 *   从当前进度反向或继续，不再依赖固定 `setTimeout`。
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
    let timeline: gsap.core.Timeline | null = null;

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
     * 播放折叠/展开时间轴。
     * 使用带标签的 Timeline 编排：内容淡出、容器折叠、内容淡入。
     */
    const play = (targets: CollapseTargets, targetCollapsed: boolean) => {
        const container = targets.container;
        if (!container) return;
        const detail = toArray(targets.detail).filter(
            (el): el is HTMLElement => Boolean(el),
        );
        const { collapsedWidth, expandedWidth } = resolveWidths(targets);

        animating.value = true;
        phase.value = targetCollapsed ? "collapsing" : "expanding";

        const tl = gsap.timeline({
            defaults: { ease: motionEase.ease },
            onComplete: () => {
                // 动画结束后交还 CSS 控制宽度
                gsap.set(container, { clearProps: "width" });
                timeline = null;
                animating.value = false;
            },
        });
        timeline = tl;

        if (targetCollapsed) {
            // 收起：内容淡出 → 容器折叠
            if (detail.length) {
                tl.to(
                    detail,
                    { autoAlpha: 0, x: 8, duration: seconds.fast },
                    "fade-out",
                );
            }
            tl.call(() => setCollapsed(true), [], "fade-out+=0.02");
            tl.to(
                container,
                { width: collapsedWidth, duration: seconds.collapse },
                "fade-out+=0.06",
            );
            tl.call(
                () => {
                    phase.value = "collapsed";
                },
                [],
                "fade-out+=0.42",
            );
        } else {
            // 展开：先恢复内容到 DOM，容器展开 → 内容淡入
            setCollapsed(false);
            tl.to(
                container,
                { width: expandedWidth, duration: seconds.collapse },
                "collapse",
            );
            if (detail.length) {
                tl.from(
                    detail,
                    { autoAlpha: 0, x: 8, duration: seconds.base },
                    "collapse+=0.12",
                );
            }
            tl.call(
                () => {
                    phase.value = "expanded";
                },
                [],
                "collapse+=0.36",
            );
        }
    };

    const toggle = () => {
        kill();

        // 减少动态效果或没有 DOM 目标时直接切换终态
        if (isReduced.value) {
            const next = !collapsed.value;
            phase.value = next ? "collapsed" : "expanded";
            setCollapsed(next);
            return;
        }

        const targets = options.targets?.();
        if (!targets?.container) {
            const next = !collapsed.value;
            phase.value = next ? "collapsed" : "expanded";
            setCollapsed(next);
            return;
        }

        play(targets, !collapsed.value);
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