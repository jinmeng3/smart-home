import { nextTick, onMounted, onScopeDispose, ref, type Ref } from "vue";
import { useReducedMotion } from "./useReducedMotion";

interface AutoScrollOptions {
  bottomThreshold?: number;
}

export const useAutoScroll = (
  container: Ref<HTMLElement | null>,
  options: AutoScrollOptions = {},
) => {
  const { prefersReducedMotion } = useReducedMotion();
  const shouldStickToBottom = ref(true);
  const bottomThreshold = options.bottomThreshold ?? 80;
  let frameId = 0;
  let resizeObserver: ResizeObserver | null = null;

  const isNearBottom = () => {
    if (!container.value) return true;
    const { scrollHeight, scrollTop, clientHeight } = container.value;
    return scrollHeight - scrollTop - clientHeight <= bottomThreshold;
  };

  const updateStickiness = () => {
    shouldStickToBottom.value = isNearBottom();
  };

  const scrollToBottom = async (force = false) => {
    await nextTick();
    if (!container.value || (!force && !shouldStickToBottom.value)) return;
    if (frameId) window.cancelAnimationFrame(frameId);
    frameId = window.requestAnimationFrame(() => {
      container.value?.scrollTo({
        top: container.value.scrollHeight,
        behavior:
          prefersReducedMotion.value ? "auto" : force ? "smooth" : "auto",
      });
      frameId = 0;
    });
  };

  const onContentResize = () => {
    if (shouldStickToBottom.value) {
      void scrollToBottom(false);
    }
  };

  onMounted(() => {
    const el = container.value;
    if (!el) return;
    resizeObserver = new ResizeObserver(onContentResize);
    resizeObserver.observe(el);
  });

  onScopeDispose(() => {
    resizeObserver?.disconnect();
    resizeObserver = null;
    if (frameId) window.cancelAnimationFrame(frameId);
  });

  return {
    scrollToBottom,
    shouldStickToBottom,
    updateStickiness,
  };
};