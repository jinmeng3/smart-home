import { onMounted, onScopeDispose, ref, type Ref } from "vue";
import {
    gsap,
    type MotionMode,
    useMotionMode,
} from "../motion";

/**
 * GSAP 作用域结果。
 *
 * 使用 `create` 注册动画，`revert` 手动清理。
 * 组件销毁时自动调用 `revert`，确保无残留 Tween、Timeline 或内联样式。
 */
export interface UseGsapScopeResult {
    /** 根元素 ref，用于限定选择器作用域 */
    root: Ref<HTMLElement | null>;
/**
     * 创建 GSAP 作用域。
     *
     * 可安全地在 setup 或 onMounted 前调用——尚未挂载时会排队，
     * `onMounted` 后统一执行。`setup` 回调中创建的 Tween/Timeline 会被
     * 作用域自动追踪。支持在回调内使用 `self.add(name, fn)` 注册事件
     * 处理函数，其内部创建的动画也会被追踪。
     */
    create: (setup: (self: gsap.Context) => void) => void;
    /** 手动清理（revert）所有该作用域下的动画 */
    revert: () => void;
    /** 当前动画模式 */
    mode: Readonly<Ref<MotionMode>>;
    /** 是否减少动态效果（reduced 或 off 模式） */
    isReduced: Readonly<Ref<boolean>>;
}

type GsapSetup = (self: gsap.Context) => void;

/**
 * 创建 GSAP 作用域 composable。
 *
 * 每个动画组件统一通过此 composable 创建：
 * - 在 `onMounted` 后创建 GSAP 动画。
 * - 通过 `gsap.context(callback, root)` 限定选择器作用域。
 * - `onScopeDispose` 自动调用 `revert()` 清理。
 * - 配合 `gsap.matchMedia()` 处理断点和减少动态效果。
 *
 * @example
 * ```ts
 * const { root, create, isReduced } = useGsapScope();
 * create((self) => {
 *   gsap.to(root.value, { autoAlpha: 1, duration: 0.3 });
 *   const mm = gsap.matchMedia();
 *   mm.add("(min-width: 768px)", () => {
 *     gsap.to(".element", { x: 100 });
 *   });
 *   self.add(() => mm.revert());
 * });
 * ```
 */
export const useGsapScope = (): UseGsapScopeResult => {
    const root = ref<HTMLElement | null>(null);
    const contexts: gsap.Context[] = [];
    const queuedSetups: GsapSetup[] = [];
    const { mode, isReduced } = useMotionMode();

    const runSetup = (setup: GsapSetup) => {
        const el = root.value;
        if (!el) return;
        contexts.push(gsap.context(setup, el));
    };

    const create = (setup: GsapSetup) => {
        if (root.value) {
            runSetup(setup);
        } else {
            queuedSetups.push(setup);
        }
    };

    const revert = () => {
        for (let i = contexts.length - 1; i >= 0; i--) {
            contexts[i]?.revert();
        }
        contexts.length = 0;
        queuedSetups.length = 0;
    };

    onMounted(() => {
        queuedSetups.splice(0).forEach(runSetup);
    });

    onScopeDispose(() => {
        revert();
    });

    return {
        root,
        create,
        revert,
        mode,
        isReduced,
    };
};