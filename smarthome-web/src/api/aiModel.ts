import { apiRequest } from "./client";

export interface AIModelRead {
  id: number;
  name: string;
  provider: string;
  api_endpoint: string;
  parameters: Record<string, unknown>;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

interface AIModelUpdate {
  name?: string;
  provider?: string;
  api_endpoint?: string;
  api_key?: string;
  parameters?: Record<string, unknown>;
  temperature?: number;
  max_tokens?: number;
  is_active?: boolean;
  description?: string | null;
}

export const getAIModel = () => apiRequest<AIModelRead>("/api/ai_model/model");

export const listAIModels = () =>
  apiRequest<AIModelRead[]>("/api/ai_model/models");

export const activateAIModel = (modelId: number) =>
  apiRequest<AIModelRead>(`/api/ai_model/models/${modelId}/activate`, {
    method: "POST",
  });

export const createAIModel = (
  payload: Required<Pick<AIModelUpdate, "name" | "provider" | "api_endpoint">> &
    AIModelUpdate,
) =>
  apiRequest<AIModelRead>("/api/ai_model/model", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateAIModel = (payload: AIModelUpdate) =>
  apiRequest<AIModelRead>("/api/ai_model/model", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const deleteAIModel = () =>
  apiRequest<void>("/api/ai_model/model", {
    method: "DELETE",
  });
