import { useMotionMode } from "../motion";

/**
 * 减少动态效果检测。
 *
 * 兼容旧版导入路径，内部委托给统一的 `useMotionMode`。
 * 新代码请直接使用 `useMotionMode`。
 *
 * @deprecated 使用 `useMotionMode` 替代
 */
export const useReducedMotion = () => {
  const { isReduced } = useMotionMode();

  return {
    prefersReducedMotion: isReduced,
  };
};