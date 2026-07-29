import { nextTick, watch, type Ref } from 'vue'
import { useReducedMotion } from './useReducedMotion'

export const useAutoScroll = (container: Ref<HTMLElement | null>, dependency: Ref<number>) => {
  const { prefersReducedMotion } = useReducedMotion()

  watch(dependency, async () => {
    await nextTick()

    if (!container.value) {
      return
    }

    container.value.scrollTo({
      top: container.value.scrollHeight,
      behavior: prefersReducedMotion.value ? 'auto' : 'smooth',
    })
  })
}
