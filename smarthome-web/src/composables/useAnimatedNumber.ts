import { computed, onScopeDispose, ref, watch, type Ref } from "vue";
import { gsap } from "../motion/gsap";
import { useMotionMode } from "../motion/motionMode";

interface UseAnimatedNumberOptions {
  startValue: number;
  endValue: Ref<number>;
  duration?: number;
  decimals?: number;
  suffix?: string;
}

/**
 * 基于 GSAP 的数字补间 composable。
 *
 * 使用 GSAP 对普通对象属性补间，替换自建 rAF 循环：
 * - 目标值更新时使用 `overwrite: "auto"`，自动覆盖旧 Tween。
 * - 减少动态效果模式直接设为终值。
 * - 组件销毁时主动 kill Tween。
 */
export const useAnimatedNumber = (options: UseAnimatedNumberOptions) => {
  const { isReduced } = useMotionMode();
  const value = ref(options.startValue);
  let activeTween: gsap.core.Tween | null = null;

  const decimals = options.decimals ?? 0;
  const duration = options.duration ?? 600;

  const animateTo = (nextValue: number) => {
    // 减少动态效果：直接呈现终值
    if (isReduced.value) {
      activeTween?.kill();
      activeTween = null;
      value.value = nextValue;
      return;
    }

    // GSAP 对 ref 的 .value 属性补间，reactive 更新自动驱动 displayValue
    activeTween = gsap.to(value, {
      value: nextValue,
      duration: duration / 1000,
      ease: "power3.out",
      overwrite: "auto",
      onComplete: () => {
        activeTween = null;
        // 确保最终值精确（浮点误差修正）
        value.value = nextValue;
      },
    });
  };

  // 监听动态模式变化：切换为减少时立即跳至终值
  watch(isReduced, (reduced) => {
    if (reduced && activeTween) {
      activeTween.kill();
      activeTween = null;
      value.value = options.endValue.value;
    }
  });

  watch(options.endValue, animateTo, { immediate: true });

  onScopeDispose(() => {
    activeTween?.kill();
    activeTween = null;
  });

  const displayValue = computed(
    () => `${value.value.toFixed(decimals)}${options.suffix ?? ""}`,
  );

  return {
    displayValue,
    value,
  };
};