import { apiRequest } from "./client";

export type ApiProtocol =
  | "openai-completions"
  | "openai-responses"
  | "azure-openai-responses"
  | "openai-codex-responses"
  | "anthropic-messages"
  | "bedrock-converse-stream";

export interface AIModelRead {
  id: number;
  name: string;
  provider: string;
  api: ApiProtocol;
  api_endpoint: string;
  parameters: Record<string, unknown>;
  compat: Record<string, unknown> | null;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  has_api_key: boolean;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AIModelPayload {
  name?: string;
  provider?: string;
  api?: ApiProtocol;
  api_endpoint?: string;
  api_key?: string;
  parameters?: Record<string, unknown>;
  compat?: Record<string, unknown> | null;
  temperature?: number;
  max_tokens?: number;
  is_active?: boolean;
  description?: string | null;
}

export const getAIModel = () =>
  apiRequest<AIModelRead>("/api/ai_model/model");

export const listAIModels = () =>
  apiRequest<AIModelRead[]>("/api/ai_model/models");

export interface AIModelProvider {
  id: string;
}

/** 获取受支持的供应商列表（弹窗下拉选项用）。 */
export const getSupportedProviders = () =>
  apiRequest<AIModelProvider[]>("/api/ai_model/providers");

export const activateAIModel = (modelId: number) =>
  apiRequest<AIModelRead>(`/api/ai_model/models/${modelId}/activate`, {
    method: "POST",
  });

export const createAIModel = (payload: AIModelPayload) =>
  apiRequest<AIModelRead>("/api/ai_model/model", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateAIModel = (payload: AIModelPayload) =>
  apiRequest<AIModelRead>("/api/ai_model/model", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const updateAIModelById = (modelId: number, payload: AIModelPayload) =>
  apiRequest<AIModelRead>(`/api/ai_model/models/${modelId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const deleteAIModel = () =>
  apiRequest<void>("/api/ai_model/model", {
    method: "DELETE",
  });

export const deleteAIModelById = (modelId: number) =>
  apiRequest<void>(`/api/ai_model/models/${modelId}`, {
    method: "DELETE",
  });

export interface AIModelTestResult {
  ok: boolean;
  latency_ms: number | null;
  message: string;
}

export const testSavedAIModel = (modelId: number) =>
  apiRequest<AIModelTestResult>(`/api/ai_model/models/${modelId}/ping`, {
    method: "POST",
  });

/** 测试模型连接：使用暂存配置发起最小请求，不回写配置。 */
export const testAIModelConnection = (payload: AIModelPayload & {
  max_tokens?: number;
}) =>
  apiRequest<AIModelTestResult>("/api/ai_model/ping", {
    method: "POST",
    body: JSON.stringify({
      name: payload.name,
      provider: payload.provider,
      api: payload.api,
      api_endpoint: payload.api_endpoint,
      ...(payload.api_key ? { api_key: payload.api_key } : {}),
      parameters: payload.parameters ?? {},
      ...(payload.compat ? { compat: payload.compat } : {}),
      temperature: payload.temperature ?? 0.7,
      max_tokens: payload.max_tokens ?? 1024,
    }),
  });
