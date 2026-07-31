import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  login as apiLogin,
  register as apiRegister,
  type LoginPayload,
  type LoginResult,
  type RegisterPayload,
} from "../api/auth";

const tokenKey = "smart-home-access-token";

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
    window.sessionStorage.setItem(
      "smart-home-current-user-id",
      String(result.user.id),
    );
    loginVisible.value = false;
  };

  const login = async (payload: LoginPayload) => {
    const result = await apiLogin(payload);
    saveSession(result);
  };

  const register = async (payload: RegisterPayload) => {
    saveSession(await apiRegister(payload));
  };

  return {
    accessToken,
    isAuthenticated,
    login,
    loginVisible,
    openLogin,
    register,
  };
});
