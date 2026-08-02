export const authExpiredEvent = "smart-home-auth-expired";
export const tokenKey = "smart-home-access-token";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

interface ApiResponse<T> {
  code: number;
  message?: string;
  data: T;
}

const isApiResponse = <T>(data: unknown): data is ApiResponse<T> => {
  return (
    typeof data === "object" &&
    data !== null &&
    "code" in data &&
    "data" in data
  );
};

const clearAuthSession = () => {
  window.sessionStorage.removeItem(tokenKey);
  window.dispatchEvent(new Event(authExpiredEvent));
};

export const parseResponse = async <T>(response: Response): Promise<T> => {
  if (response.ok) {
    if (response.status === 204) {
      return undefined as T;
    }

    const data = (await response.json()) as T | ApiResponse<T>;

    if (isApiResponse<T>(data)) {
      if (data.code !== 0) {
        throw new ApiError(data.message ?? "请求失败", response.status);
      }

      return data.data;
    }

    return data;
  }

  const data = await response.json().catch(() => ({ detail: "请求失败" }));

  if (response.status === 401) {
    clearAuthSession();
  }

  throw new ApiError(data.detail ?? data.message ?? "请求失败", response.status);
};

export const createApiHeaders = (init?: HeadersInit) => {
  const headers = new Headers(init);
  const accessToken = window.sessionStorage.getItem(tokenKey);

  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  return headers;
};

export const apiRequest = async <T>(
  path: string,
  init: RequestInit = {},
): Promise<T> => {
  const headers = createApiHeaders(init.headers);

  if (!(init.body instanceof FormData) && init.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, {
    ...init,
    headers,
  });

  return parseResponse<T>(response);
};
