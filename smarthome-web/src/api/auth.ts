import { ApiError, apiRequest } from "./client";

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
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    name: string;
    email: string;
    avatar_url: string | null;
  };
}

interface AuthResponseDto {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  user: LoginResult["user"];
}

const mapAuthResponse = (response: AuthResponseDto): LoginResult => {
  const accessToken = response.accessToken?.trim();
  if (!accessToken) {
    throw new ApiError("登录响应缺少 accessToken", 200, 0, response);
  }

  return {
    access_token: accessToken,
    token_type: response.tokenType,
    expires_in: response.expiresIn,
    user: response.user,
  };
};

export const login = async (payload: LoginPayload) =>
  mapAuthResponse(await apiRequest<AuthResponseDto>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  }));

export const register = async (payload: RegisterPayload) =>
  mapAuthResponse(await apiRequest<AuthResponseDto>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  }));

export const logout = () =>
  apiRequest<null>("/api/auth/logout", {
    method: "POST",
  });
