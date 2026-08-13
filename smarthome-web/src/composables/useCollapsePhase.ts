import { ref, type Ref } from "vue";

/**
 * 侧栏折叠三阶段动画状态机
 *
 * 收起：expanded → collapsing(120ms) → collapsed
 * 展开：collapsed → expanding(300ms) → expanded
 *
 * `collapsed` 控制实际布局（grid 宽度），`phase` 控制内部元素动画
 */
export type CollapsePhase = "expanded" | "collapsing" | "collapsed" | "expanding";

export const useCollapsePhase = (
    initialCollapsed: boolean,
    onCollapsedChange?: (collapsed: boolean) => void,
) => {
    const collapsed = ref(initialCollapsed);
    const phase = ref<CollapsePhase>(initialCollapsed ? "collapsed" : "expanded");
    const animating = ref(false);
    let timer = 0;

    const toggle = () => {
        if (animating.value) return;
        window.clearTimeout(timer);
        animating.value = true;

        if (collapsed.value) {
            // 展开：先展开宽度，再淡入内容
            phase.value = "expanding";
            collapsed.value = false;
            onCollapsedChange?.(false);

            // 宽度动画完成后 → expanded
            timer = window.setTimeout(() => {
                phase.value = "expanded";
                animating.value = false;
            }, 300);
        } else {
            // 收起：先淡出内容，再收缩宽度
            phase.value = "collapsing";

            // 内容淡出完成后 → 切换宽度
            timer = window.setTimeout(() => {
                collapsed.value = true;
                onCollapsedChange?.(true);
                // 宽度动画完成后 → collapsed
                timer = window.setTimeout(() => {
                    phase.value = "collapsed";
                    animating.value = false;
                }, 280);
            }, 120);
        }
    };

    /** 首次加载不播放动画，直接设置最终状态 */
    const skipAnimation = () => {
        phase.value = collapsed.value ? "collapsed" : "expanded";
        animating.value = false;
    };

    return { collapsed, phase, animating, toggle, skipAnimation };
};