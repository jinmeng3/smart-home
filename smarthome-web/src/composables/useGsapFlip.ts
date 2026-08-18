import { type Ref, nextTick, onScopeDispose, getCurrentScope } from "vue";
import { gsap, registerFlip, useMotionMode } from "../motion";

export interface UseGsapFlipOptions {
    /** 列表容器 ref */
    container: Ref<HTMLElement | null>;
    /** 列表项选择器（如 `".message-item"`、`".device-row"`） */
    itemSelector: string;
    /** 动画时长（毫秒，默认 240） */
    duration?: number;
    /** 是否已禁用（折叠状态等） */
    deactivated?: Ref<boolean>;
}

/**
 * GSAP Flip 列表动画 composable。
 *
 * 在 Vue 完成数据更新前捕获列表项布局状态，DOM 更新后执行 `Flip.from()`
 * 过渡到新位置，消除 `max-height: 1000px` 等固定上限动画。
 *
 * @example
 * ```ts
 * const { flip } = useGsapFlip({
 *   container: listRef,
 *   itemSelector: ".message-item",
 * });
 *
 * // 在数据更新后（DOM 已更新）调用
 * await flip();
 * ```
 */
export const useGsapFlip = (options: UseGsapFlipOptions) => {
    const { isReduced } = useMotionMode();
    let flipLoaded = false;
    let flipState: gsap.FlipState | null = null;

    /** 在数据变更前捕获当前列表布局 */
    const capture = () => {
        if (isReduced.value) return;
        const el = options.container.value;
        if (!el) return;

        // 延迟加载 Flip 插件（首次调用时）
        if (!flipLoaded) {
            // 异步加载，但捕获需要同步——先记录状态，加载后执行
            void registerFlip().then(() => {
                flipLoaded = true;
            });
        }

        const items = el.querySelectorAll(options.itemSelector);
        if (items.length) {
            try {
                flipState = (gsap as any).Flip?.getState?.(items) ?? null;
            } catch {
                flipState = null;
            }
        } else {
            flipState = null;
        }
    };

    /** 在 DOM 更新后执行 Flip 过渡 */
    const flip = async () => {
        if (isReduced.value || !flipState) return;

        await nextTick();

        // 确保插件已加载
        if (!flipLoaded) {
            await registerFlip();
            flipLoaded = true;
        }

        const el = options.container.value;
        if (!el) return;

        const items = el.querySelectorAll(options.itemSelector);
        if (!items.length) return;

        try {
            (gsap as any).Flip.from?.(flipState, {
                duration: (options.duration ?? 240) / 1000,
                ease: "power3.out",
                absolute: true,
                onComplete: () => {
                    flipState = null;
                },
            });
        } catch {
            flipState = null;
        }
    };

    /** 捕获 + 执行一步完成 */
    const captureAndFlip = async () => {
        if (options.deactivated?.value) return;
        capture();
        await flip();
    };

    // 组件销毁时清理
    if (getCurrentScope()) {
        onScopeDispose(() => {
            flipState = null;
        });
    }

    return {
        capture,
        flip,
        captureAndFlip,
    };
};