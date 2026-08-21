import { ref, type Ref, watch, onScopeDispose, getCurrentScope } from "vue";
import { gsap, useMotionMode } from "../motion";

/**
 * 颜色强调动画选项。
 */
export interface ColorEmphasisOptions {
    /** 强调色 CSS 变量或色值（默认 `var(--color-primary)`） */
    highlightColor?: string;
    /** 动画时长（毫秒，默认 160） */
    duration?: number;
    /** 保持强调的时间（毫秒，默认 800，之后恢复） */
    holdDuration?: number;
}

/**
 * 局部颜色强调动画 composable。
 *
 * 当某个字段值发生变化时，对指定元素播放一次短促的颜色强调（160ms），
 * 然后恢复原始颜色。用于全屋总览、设置页等场景中的数字/状态变化反馈。
 *
 * - 使用 GSAP 的 `color` 和 `background-color` 属性补间。
 * - 减少动态效果模式跳过动画，直接呈现终态。
 * - 组件销毁时自动清理 Tween。
 *
 * @example
 * ```ts
 * const { emphasize, registerElement } = useColorEmphasis();
 *
 * // 注册一个响应式元素
 * const elRef = ref<HTMLElement | null>(null);
 * registerElement(elRef);
 *
 * // 监听值变化并触发强调
 * watch(() => props.value, () => emphasize());
 * ```
 */
export const useColorEmphasis = (options: ColorEmphasisOptions = {}) => {
    const { isReduced } = useMotionMode();
    const elements = ref<HTMLElement[]>([]);
    let activeTween: gsap.core.Tween | null = null;

    const highlightColor = options.highlightColor ?? "var(--color-primary)";
    const duration = (options.duration ?? 160) / 1000;
    const holdDuration = options.holdDuration ?? 800;

/**
     * 注册一个或多个需要强调的元素。
     */
    const registerElement = (el: HTMLElement | null) => {
        if (!el) return;
        if (!elements.value.includes(el)) {
            elements.value = [...elements.value, el];
        }
    };

/**
     * 批量注册多个元素。
     */
    const registerElements = (els: (HTMLElement | null)[]) => {
        const next = [...elements.value];
        for (const el of els) {
            if (el && !next.includes(el)) {
                next.push(el);
            }
        }
        elements.value = next;
    };

/**
     * 注册一个 ref 元素。
     */
    const registerRef = (elRef: Ref<HTMLElement | null>) => {
        watch(
            elRef,
            (el) => {
                if (el) registerElement(el);
            },
            { once: true },
        );
    };

/**
     * 播放一次颜色强调动画。
     *
     * - 减少动态效果模式跳过动画。
     * - 会覆盖之前的活跃 Tween。
     */
    const emphasize = () => {
        if (isReduced.value || !elements.value.length) return;

        if (activeTween) {
            activeTween.kill();
            activeTween = null;
        }

        const targets = elements.value.filter((el) => el?.isConnected);
        if (!targets.length) return;

        const originalColors = targets.map((el) => ({
            color: getComputedStyle(el).color,
        }));

        const tl = gsap.timeline({
            onComplete: () => {
                activeTween = null;
            },
        });

        tl.to(
            targets,
            {
                color: highlightColor,
                duration,
                ease: "power2.out",
            },
            0,
        );

        targets.forEach((el, i) => {
            const originalColor = originalColors[i]?.color ?? "";
            tl.to(
                el,
                {
                    color: originalColor,
                    duration,
                    ease: "power2.in",
                },
                `+=${holdDuration / 1000}`,
            );
        });
    };

/**
     * 创建一个监听数值变化的强调效果。
     *
     * @param source 被监听的响应式数值
     * @param formatter 可选格式化函数，用于比较新旧值
     */
    const watchAndEmphasize = <T>(source: Ref<T>) => {
        watch(source, () => {
            emphasize();
        });
    };

    if (getCurrentScope()) {
        onScopeDispose(() => {
            if (activeTween) {
                activeTween.kill();
                activeTween = null;
            }
        });
    }

    return {
        /** 注册单个强调目标元素 */
        registerElement,
        /** 批量注册多个强调目标元素 */
        registerElements,
        /** 注册 ref 元素（自动在挂载后注册） */
        registerRef,
        /** 播放颜色强调 */
        emphasize,
        /** 监听数值变化自动触发强调 */
        watchAndEmphasize,
    };
};