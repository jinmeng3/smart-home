import { onScopeDispose, ref } from 'vue'

export const useVisibility = () => {
  const isVisible = ref(document.visibilityState === 'visible')

  const updateVisibility = () => {
    isVisible.value = document.visibilityState === 'visible'
  }

  document.addEventListener('visibilitychange', updateVisibility)

  onScopeDispose(() => {
    document.removeEventListener('visibilitychange', updateVisibility)
  })

  return {
    isVisible,
  }
}
