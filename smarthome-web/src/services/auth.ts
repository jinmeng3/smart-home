import {
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  type LoginPayload,
  type LoginResult,
  type RegisterPayload,
} from "../api/auth";

/**
 * 认证领域服务层（DIP：store 只依赖此抽象，
 * 不直接依赖 API 实现；单一职责——仅编排认证会话）。
 */
export const authService = {
  login(payload: LoginPayload): Promise<LoginResult> {
    return apiLogin(payload);
  },

  register(payload: RegisterPayload): Promise<LoginResult> {
    return apiRegister(payload);
  },

  logout(): Promise<null> {
    return apiLogout();
  },
};
