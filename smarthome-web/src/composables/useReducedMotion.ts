import { onScopeDispose, readonly, ref } from "vue";

const prefersReducedMotion = ref(false);
let mediaQuery: MediaQueryList | null = null;
let consumers = 0;

const updatePreference = () => {
  prefersReducedMotion.value = Boolean(mediaQuery?.matches);
};

const connect = () => {
  consumers += 1;
  if (consumers === 1) {
    mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    updatePreference();
    mediaQuery.addEventListener("change", updatePreference);
  }
};

const disconnect = () => {
  consumers -= 1;
  if (consumers === 0) {
    mediaQuery?.removeEventListener("change", updatePreference);
    mediaQuery = null;
  }
};

export const useReducedMotion = () => {
  connect();
  onScopeDispose(disconnect);

  return {
    prefersReducedMotion: readonly(prefersReducedMotion),
  };
};
