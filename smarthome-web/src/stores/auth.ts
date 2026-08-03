import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  type LoginPayload,
  type LoginResult,
  type RegisterPayload,
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

  window.addEventListener(authExpiredEvent, clearSession);

  const login = async (payload: LoginPayload, closeDialog = true) => {
    const result = await apiLogin(payload);
    saveSession(result, closeDialog);
  };

  const register = async (payload: RegisterPayload, closeDialog = true) => {
    saveSession(await apiRegister(payload), closeDialog);
  };

  const logout = async (closeDialog = true) => {
    try {
      await apiLogout();
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
