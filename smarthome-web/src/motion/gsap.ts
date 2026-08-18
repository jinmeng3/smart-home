/**
 * 公共 GSAP 入口。
 *
 * - 导出同一个 `gsap` 实例，所有组件共用。
 * - 提供按需插件加载函数，避免未使用的插件进入首屏包。
 * - 插件只在应用级或公共加载模块注册一次，不在组件更新路径重复注册。
 *
 * 使用约定：
 * ```ts
 * import { gsap, registerFlip } from "../motion/gsap";
 *
 * // 首次使用时按需加载
 * await registerFlip(); // 仅加载一次，后续调用为空
 * ```
 */
import { gsap } from "gsap";

// 导出共享实例
export { gsap };

/* ------------------------------------------------------------------ */
/*  按需插件加载器                                                      */
/* ------------------------------------------------------------------ */

let flipLoaded = false;

/**
 * 按需加载 GSAP Flip 插件。
 * 用于动态列表增删与重排的动画过渡。
 *
 * 首次调用才会加载 Flip 代码并注册；后续调用为空操作。
 */
export const registerFlip = async (): Promise<void> => {
    if (flipLoaded) return;
    const { Flip } = await import("gsap/Flip");
    gsap.registerPlugin(Flip);
    flipLoaded = true;
};

let scrollTriggerLoaded = false;

/**
 * 按需加载 ScrollTrigger 插件。
 * 用于视口触发或滚动联动动画。
 *
 * 仅在对应路由/组件中调用，不进入首屏主包。
 * 动态内容改变布局后，在 `nextTick` 后按需调用一次 `ScrollTrigger.refresh()`。
 */
export const registerScrollTrigger = async (): Promise<void> => {
    if (scrollTriggerLoaded) return;
    const { ScrollTrigger } = await import("gsap/ScrollTrigger");
    gsap.registerPlugin(ScrollTrigger);
    scrollTriggerLoaded = true;
};

/* ------------------------------------------------------------------ */
/*  工具函数                                                            */
/* ------------------------------------------------------------------ */

/**
 * 获取当前设备像素比，用于判断是否需要高精度动画。
 */
export const getDevicePixelRatio = (): number =>
    typeof window !== "undefined" ? window.devicePixelRatio : 1;

/**
 * 检查是否处于低性能设备（低端设备或数据性能模式）。
 */
export const isLowPerformanceDevice = (): boolean => {
    if (typeof window === "undefined") return false;
    return (
        document.documentElement.dataset.performance === "lite" ||
        window.devicePixelRatio < 2 ||
        navigator.hardwareConcurrency <= 4
    );
};