import { nextTick, onScopeDispose, ref, type Ref } from "vue";
import { gsap, motionEase, seconds, useMotionMode } from "../motion";

/** `useCardGridEnter` 选项 */
export interface CardGridEnterOptions {
/**
     * 容器选择器（默认 `.card-grid-enter`）。
     *
     * 可传入其他同类网格容器（如 `.room-grid`）复用同一套 stagger 入场逻辑。
     */
    selector?: string;
}

/**
 * 页面/卡片入场 stagger composable。
 *
 * 替换 `styles/animations.css` 中 `.card-grid-enter > :nth-child(1..8)`
 * 的硬编码延迟表：多个同类元素统一使用 GSAP `stagger` 编排入场。
 *
 * - 减少动态效果（reduced / off）时跳过动画，元素直接呈现终态。
 * - 已入场元素通过 `WeakSet` 记忆，重复触发（如数据加载完成、展开/收起）
 *   时只对新出现的子元素播放动画。
 * - 卡片 stagger 只在首次加载成功时执行，刷新和返回页面不重播。
 * - 作用域 context 在组件销毁时统一 `revert()`，无残留 Tween 或内联样式。
 *
 * @example
 * ```ts
 * const { root, play } = useCardGridEnter();
 * watch(loading, (l) => { if (!l) void play(); });
 * ```
 */
export const useCardGridEnter = (options?: CardGridEnterOptions) => {
    const selector = options?.selector ?? ".card-grid-enter";
    const { isReduced } = useMotionMode();
    const root = ref<HTMLElement | null>(null);
    /** 已播放过入场的元素，避免重复触发时再次淡入 */
    const animated = new WeakSet<Element>();
    /** 管理中的 gsap context，销毁时统一 revert */
    const contexts: gsap.Context[] = [];
    /** 是否首次加载已执行过，刷新和返回页面不重播 */
    let playedOnce = false;

    const findItems = (): Element[] => {
        const el = root.value;
        if (!el) return [];
        const containers = el.querySelectorAll<HTMLElement>(selector);
        const items: Element[] = [];
        containers.forEach((container) => {
            Array.from(container.children).forEach((child) => {
                if (!animated.has(child)) {
                    animated.add(child);
                    items.push(child);
                }
            });
        });
        return items;
    };

    /** 播放卡片网格 stagger 入场（需在数据渲染后调用） */
    const play = async () => {
        if (isReduced.value || !root.value) return;
        if (playedOnce) return;
        await nextTick();
        const items = findItems();
        if (!items.length) return;

        const staggerDuration = Math.min(0.08, 0.42 / Math.max(items.length, 1));

        const ctx = gsap.context(() => {
            gsap.from(items, {
                autoAlpha: 0,
                y: 14,
                duration: seconds.pageEnter,
                ease: motionEase.ease,
                stagger: staggerDuration,
                overwrite: "auto",
                onComplete: () => {
                    playedOnce = true;
                    gsap.set(items, {
                        clearProps: "transform,opacity,visibility",
                    });
                },
            });
        }, root.value);
        contexts.push(ctx);
    };

    /** 手动回滚全部入场动画（一般由组件销毁自动触发） */
    const revert = () => {
        contexts.forEach((ctx) => ctx.revert());
        contexts.length = 0;
    };

    /** 重置 playedOnce 状态，允许再次播放入场动画 */
    const reset = () => {
        playedOnce = false;
    };

    onScopeDispose(() => {
        revert();
    });

    return {
        /** 绑定到包含 `.card-grid-enter` 容器的根元素 */
        root,
        /** 播放 stagger 入场；数据渲染完成后调用一次 */
        play,
        /** 手动清理入场动画 */
        revert,
        /** 重置已播放状态，允许再次播放 */
        reset,
    } as {
        root: Ref<HTMLElement | null>;
        play: () => Promise<void>;
        revert: () => void;
        reset: () => void;
    };
};