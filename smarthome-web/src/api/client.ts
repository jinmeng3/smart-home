/**
 * 统一请求层（低端机性能优化方案 — 3. 修正 API 适配层）。
 *
 * 三个入口：
 *  - apiRequest<T>   ：解析 { code, message, data } 包装响应
 *  - rawRequest<T>   ：处理 OpenAI 兼容的非包装响应
 *  - streamRequest   ：统一 SSE 读取、分片缓冲、取消和错误解析
 *
 * ApiError 扩展：status、code、details、fieldErrors。
 * 401 仅触发一次会话清理；422 校验数组转为用户可读字段错误。
 * AbortSignal、请求超时、幂等键通过 RequestInit 透传。
 */

export const authExpiredEvent = "smart-home-auth-expired";
export const tokenKey = "smart-home-access-token";

let authExpiredHandled = false;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: number = 0,
    readonly details: unknown = null,
    readonly fieldErrors: Record<string, string> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ApiResponse<T> {
  code: number;
  message?: string;
  data: T | null;
}

const isApiResponse = <T>(data: unknown): data is ApiResponse<T> => {
  return (
    typeof data === "object" &&
    data !== null &&
    "code" in data &&
    "data" in data
  );
};

const parseFieldErrors = (data: unknown): Record<string, string> => {
  if (!data || typeof data !== "object") return {};
  const d = data as Record<string, unknown>;
  if (!Array.isArray(d.errors)) return {};
  const fields: Record<string, string> = {};
  for (const err of d.errors) {
    if (err && typeof err === "object") {
      const e = err as Record<string, unknown>;
      const field = e.field;
      const message = e.message;
      if (typeof field === "string" && typeof message === "string" && field) {
        fields[field] = message;
      }
    }
  }
  return fields;
};

const clearAuthSession = () => {
  window.sessionStorage.removeItem(tokenKey);
  if (!authExpiredHandled) {
    authExpiredHandled = true;
    window.dispatchEvent(new Event(authExpiredEvent));
  }
};

const markRequestSucceeded = () => {
  authExpiredHandled = false;
};

/** 解析后端 ApiResponse 包装响应，返回 `data` 字段。 */
export const parseResponse = async <T>(
  response: Response,
  handleUnauthorized = true,
): Promise<T> => {
  const body = await response.text().catch(() => "");

  if (response.ok) {
    markRequestSucceeded();

    if (response.status === 204) {
      return undefined as T;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(body);
    } catch {
      throw new ApiError("响应格式错误", response.status);
    }

    if (isApiResponse<T>(parsed)) {
      const apiResp = parsed as ApiResponse<T>;
      if (apiResp.code !== 0) {
        const fieldErrors = parseFieldErrors(apiResp.data);
        throw new ApiError(
          apiResp.message ?? "请求失败",
          response.status,
          apiResp.code,
          apiResp.data,
          fieldErrors,
        );
      }
      return apiResp.data as T;
    }

    // 非包装响应（如 SSE 之外的 OpenAI 响应）
    return parsed as T;
  }

  // === 错误处理 ===

  let parsed: unknown;
  try {
    parsed = JSON.parse(body);
  } catch {
    parsed = { detail: body || "请求失败" };
  }

  if (response.status === 401 && handleUnauthorized) {
    clearAuthSession();
    throw new ApiError(
      "登录状态已失效，请重新登录",
      response.status,
      40100,
      parsed,
    );
  }

  const apiResp = isApiResponse(parsed) ? (parsed as ApiResponse<unknown>) : null;

  if (response.status === 422 && apiResp) {
    const fieldErrors = parseFieldErrors(apiResp.data);
    throw new ApiError(
      apiResp.message ?? "请求参数校验失败",
      response.status,
      42200,
      apiResp.data,
      fieldErrors,
    );
  }

  throw new ApiError(
    apiResp?.message ?? (parsed as Record<string, unknown>)?.detail as string ?? "请求失败",
    response.status,
    apiResp?.code ?? 0,
    apiResp?.data ?? parsed,
  );
};

export const createApiHeaders = (init?: HeadersInit) => {
  const headers = new Headers(init);
  const accessToken = window.sessionStorage.getItem(tokenKey)?.trim();
  const hasValidTokenValue =
    accessToken && accessToken !== "undefined" && accessToken !== "null";

  if (hasValidTokenValue && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  } else if (accessToken && !hasValidTokenValue) {
    window.sessionStorage.removeItem(tokenKey);
  }

  return headers;
};

/**
 * 请求后端 ApiResponse 包装接口。
 * 自动添加 Content-Type 和 Authorization 头。
 */
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

  return parseResponse<T>(response, headers.has("Authorization"));
};

/**
 * 请求非包装原始响应（如 OpenAI 兼容接口）。
 * 不解析 ApiResponse 外壳，直接返回 JSON 体。
 */
export const rawRequest = async <T>(
  path: string,
  init: RequestInit = {},
): Promise<T> => {
  const headers = createApiHeaders(init.headers);

  if (!(init.body instanceof FormData) && init.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...init, headers });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    let parsed: unknown;
    try {
      parsed = JSON.parse(body);
    } catch {
      parsed = { detail: body || "请求失败" };
    }
    if (response.status === 401 && headers.has("Authorization")) {
      clearAuthSession();
    }
    throw new ApiError(
      (parsed as Record<string, unknown>)?.detail as string ?? "请求失败",
      response.status,
      0,
      parsed,
    );
  }

  markRequestSucceeded();
  return response.json() as Promise<T>;
};

/**
 * SSE 流式读取（统一 SSE 读取、分片缓冲、取消和错误解析）。
 * 逐行回调 onLine，调用方按需解析行内容。
 */
export const streamRequest = async (
  path: string,
  onLine: (line: string) => void,
  init: RequestInit = {},
  signal?: AbortSignal,
): Promise<void> => {
  const headers = createApiHeaders(init.headers);
  headers.set("Accept", "text/event-stream");

  if (!(init.body instanceof FormData) && init.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...init, headers, signal });

  if (!response.ok) {
    await parseResponse<never>(response, headers.has("Authorization"));
    return;
  }

  markRequestSucceeded();

  if (!response.body) {
    throw new ApiError("SSE 响应没有 body", 0);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        onLine(line.trim());
      }
    }
    buffer += decoder.decode();
    if (buffer.trim()) onLine(buffer.trim());
  } finally {
    if (signal?.aborted) {
      await reader.cancel().catch(() => undefined);
    }
    reader.releaseLock();
  }
};
