/**
 * 动画公共入口。
 *
 * 所有 GSAP 相关能力从这里导出，页面不得直接 import "gsap" 各自初始化。
 */
export {
    gsap,
    registerFlip,
    registerScrollTrigger,
    getDevicePixelRatio,
    isLowPerformanceDevice,
} from "./gsap";
export type { MotionMode } from "./motionMode";
export { useMotionMode } from "./motionMode";
export {
    motionDuration,
    motionEase,
    seconds,
    toSeconds,
} from "./tokens";