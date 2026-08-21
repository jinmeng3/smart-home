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
import { useHouseholdStore } from "./households";
import { useSettingsStore } from "./settings";

export const useAuthStore = defineStore("auth", () => {
  const storedAccessToken = window.sessionStorage.getItem(tokenKey);
  const initialAccessToken =
    storedAccessToken &&
    storedAccessToken !== "undefined" &&
    storedAccessToken !== "null"
      ? storedAccessToken
      : null;

  if (!initialAccessToken) window.sessionStorage.removeItem(tokenKey);

  const accessToken = ref(initialAccessToken);
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
    useHouseholdStore().clear();
    useSettingsStore().resetAccountState();
  };

  const handleAuthExpired = () => {
    clearSession();
    loginVisible.value = true;
  };

  window.addEventListener(authExpiredEvent, handleAuthExpired);

  const login = async (payload: LoginPayload, closeDialog = true) => {
    const result = await apiLogin(payload);
    saveSession(result, closeDialog);
  };

  const register = async (payload: RegisterPayload, closeDialog = true) => {
    saveSession(await apiRegister(payload), closeDialog);
  };

  const logout = async (closeDialog = true) => {
    try {
      await apiLogout().catch(() => undefined);
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
