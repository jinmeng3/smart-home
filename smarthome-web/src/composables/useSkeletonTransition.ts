import { type Ref, nextTick, onScopeDispose, watch, getCurrentScope } from "vue";
import { gsap, motionEase, seconds, useMotionMode } from "../motion";

/**
 * 骨架屏到真实内容的交叉淡入过渡 composable。
 *
 * 当 loading 从 true 变为 false 时，对容器内的元素播放淡入动画。
 * - 减少动态效果模式跳过动画，直接呈现终态。
 * - 组件销毁时自动清理 Tween。
 *
 * @example
 * ```ts
 * const containerRef = ref<HTMLElement | null>(null);
 * const { play } = useSkeletonTransition(containerRef, loading);
 * // loading 从 true → false 时自动触发
 * ```
 */
export const useSkeletonTransition = (
    container: Ref<HTMLElement | null>,
    loading: Ref<boolean>,
) => {
    const { isReduced } = useMotionMode();
    let activeTween: gsap.core.Tween | null = null;

    const kill = () => {
        if (activeTween) {
            activeTween.kill();
            activeTween = null;
        }
    };

    /** 手动触发交叉淡入过渡 */
    const play = async () => {
        if (isReduced.value || !container.value) return;
        kill();

        await nextTick();

        const el = container.value;
        if (!el) return;

        // 对容器内所有直属子元素做淡入
        const children = Array.from(el.children).filter(
            (child) => child instanceof HTMLElement,
        ) as HTMLElement[];

        if (!children.length) return;

        // 设置初始状态
        gsap.set(children, { autoAlpha: 0, y: 8 });

        activeTween = gsap.to(children, {
            autoAlpha: 1,
            y: 0,
            duration: seconds.base,
            ease: motionEase.ease,
            stagger: 0.04,
            overwrite: "auto",
            onComplete: () => {
                // 交还 CSS 控制
                gsap.set(children, {
                    clearProps: "transform,opacity,visibility",
                });
                activeTween = null;
            },
        });
    };

    // 监听 loading 状态变化：true → false 时触发过渡
    watch(loading, (isLoading) => {
        if (!isLoading) {
            void play();
        }
    });

    // 组件销毁时清理
    if (getCurrentScope()) {
        onScopeDispose(kill);
    }

    return {
        /** 手动触发过渡 */
        play,
        /** 清理活跃 Tween */
        kill,
    };
};