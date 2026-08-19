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
 * 时序修正：
 * - capture 必须在任何 await 之前同步执行，此时 DOM 仍是旧状态；
 *   Vue 的 DOM 更新被批量调度为微任务，若在 capture 前 await，
 *   会捕获到新状态导致 Flip 变成空操作。
 * - Flip 插件在 composable 创建时即开始预加载，保证 watcher 触发时
 *   已可同步捕获。
 * - 若捕获时插件尚未就绪（极端首次情况），放弃本次动画而不是从
 *   新 DOM 重新捕获（那会得到错误的首帧）。
 *
 * @example
 * ```ts
 * const { capture, flip } = useGsapFlip({
 *   container: listRef,
 *   itemSelector: ".message-item",
 * });
 *
 * // 在数据变更前调用 capture
 * capture();
 * // 数据变更后，DOM 更新前调用
 * await flip();
 * ```
 */
export const useGsapFlip = (options: UseGsapFlipOptions) => {
    const { isReduced } = useMotionMode();
    let flipLoaded = false;
    let flipInitPromise: Promise<void> | null = null;
    let flipState: gsap.FlipState | null = null;

    /** 确保 Flip 插件已加载（首次异步加载，后续同步） */
    const ensureFlipLoaded = async (): Promise<void> => {
        if (flipLoaded) return;
        if (!flipInitPromise) {
            flipInitPromise = registerFlip().then(() => {
                flipLoaded = true;
            });
        }
        await flipInitPromise;
    };

    /** 在数据变更前同步捕获当前列表布局（不得在 await 之后调用） */
    const capture = () => {
        if (isReduced.value) return;
        // 插件未就绪时无法捕获——放弃本次动画，等待下次
        if (!flipLoaded) {
            flipState = null;
            return;
        }
        const el = options.container.value;
        if (!el) return;

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

        // 确保插件已加载（捕获时已就绪，此处应为同步返回）
        await ensureFlipLoaded();

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
        // 同步捕获旧状态——必须在任何 await 之前，确保捕获到变更前的 DOM
        capture();
        await flip();
    };

    // composable 创建时即开始预加载插件，保证后续 watcher 同步捕获可用
    void ensureFlipLoaded();

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
