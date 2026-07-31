import { apiRequest } from "./client";

export interface LoginPayload {
  account: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface LoginResult {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: {
    id: number;
    name: string;
    email: string;
    avatar_url: string | null;
  };
}

export const login = (payload: LoginPayload) =>
  apiRequest<LoginResult>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const register = (payload: RegisterPayload) =>
  apiRequest<LoginResult>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
