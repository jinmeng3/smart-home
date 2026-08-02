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

  const saveSession = (result: LoginResult) => {
    accessToken.value = result.access_token;
    window.sessionStorage.setItem(tokenKey, result.access_token);
    loginVisible.value = false;
  };

  const clearSession = () => {
    accessToken.value = null;
    window.sessionStorage.removeItem(tokenKey);
  };

  window.addEventListener(authExpiredEvent, clearSession);

  const login = async (payload: LoginPayload) => {
    const result = await apiLogin(payload);
    saveSession(result);
  };

  const register = async (payload: RegisterPayload) => {
    saveSession(await apiRegister(payload));
  };

  const logout = async () => {
    try {
      await apiLogout();
    } finally {
      clearSession();
      loginVisible.value = false;
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
