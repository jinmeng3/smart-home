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

export const deleteAIModel = () =>
  apiRequest<void>("/api/ai_model/model", {
    method: "DELETE",
  });