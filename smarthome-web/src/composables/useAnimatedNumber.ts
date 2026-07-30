import { computed, onBeforeUnmount, ref, watch, type Ref } from "vue";
import { useReducedMotion } from "./useReducedMotion";

interface UseAnimatedNumberOptions {
  startValue: number;
  endValue: Ref<number>;
  duration?: number;
  decimals?: number;
  suffix?: string;
}

export const useAnimatedNumber = (options: UseAnimatedNumberOptions) => {
  const { prefersReducedMotion } = useReducedMotion();
  const value = ref(options.startValue);
  let frameId = 0;

  const decimals = options.decimals ?? 0;
  const duration = options.duration ?? 600;

  const stop = () => {
    if (frameId) {
      window.cancelAnimationFrame(frameId);
      frameId = 0;
    }
  };

  const animateTo = (nextValue: number) => {
    stop();

    if (prefersReducedMotion.value) {
      value.value = nextValue;
      return;
    }

    const initialValue = value.value;
    const delta = nextValue - initialValue;
    const startTime = performance.now();

    const tick = (time: number) => {
      const progress = Math.min((time - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      value.value = initialValue + delta * eased;

      if (progress < 1) {
        frameId = window.requestAnimationFrame(tick);
      }
    };

    frameId = window.requestAnimationFrame(tick);
  };

  watch(options.endValue, animateTo, { immediate: true });

  onBeforeUnmount(stop);

  const displayValue = computed(
    () => `${value.value.toFixed(decimals)}${options.suffix ?? ""}`,
  );

  return {
    displayValue,
    value,
  };
};
