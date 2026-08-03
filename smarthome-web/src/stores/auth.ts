import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { authService } from "../services/auth";
import type {
  LoginPayload,
  LoginResult,
  RegisterPayload,
} from "../api/auth";
import { authExpiredEvent, tokenKey } from "../api/client";

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref(window.sessionStorage.getItem(tokenKey));
  const loginVisible = ref(false);
  const isAuthenticated = computed(() => Boolean(accessToken.value));

  const openLogin = () => {
    loginVisible.value = true;
  };

  const saveSession = (result: LoginResult, closeDialog = true) => {
    accessToken.value = result.access_token;
    window.sessionStorage.setItem(tokenKey, result.access_token);
    if (closeDialog) loginVisible.value = false;
  };

  const clearSession = () => {
    accessToken.value = null;
    window.sessionStorage.removeItem(tokenKey);
  };

  const handleAuthExpired = () => {
    clearSession();
    loginVisible.value = true;
  };

  window.addEventListener(authExpiredEvent, handleAuthExpired);

  const login = async (payload: LoginPayload, closeDialog = true) => {
    const result = await authService.login(payload);
    saveSession(result, closeDialog);
  };

  const register = async (payload: RegisterPayload, closeDialog = true) => {
    saveSession(await authService.register(payload), closeDialog);
  };

  const logout = async (closeDialog = true) => {
    try {
      await authService.logout().catch(() => undefined);
    } finally {
      clearSession();
      if (closeDialog) loginVisible.value = false;
    }
  };

  return {
    accessToken,
    isAuthenticated,
    login,
    loginVisible,
    logout,
    openLogin,
    register,
  };
});
