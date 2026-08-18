import { computed, getCurrentScope, onScopeDispose, readonly, ref } from "vue";

/**
 * 统一的动态效果模式。
 *
 * - `full`：完整动画
 * - `reduced`：减少动态效果（系统 prefer-reduced-motion 或性能模式 lite）
 * - `off`：关闭动画（`data-motion="off"`，优先级最高）
 *
 * MotionMode 综合系统 `prefers-reduced-motion`、`data-motion="off"` 和
 * `data-performance="lite"` 计算：
 *
 * 1. 显式关闭（`data-motion="off"`）优先级最高；
 * 2. 其次系统减少动态效果或 `data-performance="lite"`；
 * 3. 最后是完整动画。
 */
export type MotionMode = "full" | "reduced" | "off";

const ROOT_SELECTOR = ":root";

const computeMotionMode = (): MotionMode => {
    const root = document.documentElement;
    const dataMotion = root.dataset.motion;
    if (dataMotion === "off") {
        return "off";
    }

    const systemReduced = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
    ).matches;
    const performanceLite = root.dataset.performance === "lite";

    if (systemReduced || performanceLite) {
        return "reduced";
    }

    return "full";
};

const mode = ref<MotionMode>(computeMotionMode());
let consumers = 0;
let mediaQuery: MediaQueryList | null = null;
let observer: MutationObserver | null = null;

const updateMode = () => {
    mode.value = computeMotionMode();
};

const connect = () => {
    consumers += 1;
    if (consumers > 1) return;

    updateMode();
    mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    mediaQuery.addEventListener("change", updateMode);

    observer = new MutationObserver((mutations) => {
        const relevantChange = mutations.some(
            (mutation) =>
                mutation.type === "attributes" &&
                (mutation.attributeName === "data-motion" ||
                    mutation.attributeName === "data-performance"),
        );
        if (relevantChange) updateMode();
    });
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-motion", "data-performance"],
    });
};

const disconnect = () => {
    consumers -= 1;
    if (consumers > 0) return;

    mediaQuery?.removeEventListener("change", updateMode);
    mediaQuery = null;
    observer?.disconnect();
    observer = null;
};

/**
 * 统一动画模式入口。
 *
 * 可在组件 setup、composable 或 Pinia store 中调用；组件实例销毁时自动
 * 断开订阅（引用计数归零后才真正移除监听，Store 长时间持有也安全）。
 */
export const useMotionMode = () => {
    connect();
    if (getCurrentScope()) {
        onScopeDispose(disconnect);
    }

    return {
        /** 完整 / 减少 / 关闭 */
        mode: readonly(mode),
        /** 是否减少动态效果（reduced 或 off 都应直接呈现终态） */
        isReduced: readonly(
            computed(() => mode.value === "reduced" || mode.value === "off"),
        ),
    };
};

