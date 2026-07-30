import { apiRequest } from "./client";

export interface AIModelRead {
  name: string;
  provider: string;
  api_endpoint: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AIModelUpdate {
  name?: string;
  provider?: string;
  api_endpoint?: string;
  api_key?: string;
  temperature?: number;
  max_tokens?: number;
  is_active?: boolean;
  description?: string | null;
}

export const getAIModel = () => apiRequest<AIModelRead>("/api/ai_model/model");

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
