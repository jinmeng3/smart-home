import { apiRequest } from "./client";
import type {
  Scene,
  SceneExecution,
  SceneFilters,
  SceneInput,
  SceneSummary,
  SceneTemplate,
  SceneTemplateUseInput,
  SceneLog,
  SceneLogListResponse,
  ScenePreview,
  SceneOrderItem,
  SceneOrderResult,
  SceneBatchEnabledInput,
  SceneBatchEnabledResult,
  SceneBatchScheduleInput,
  SceneBatchScheduleResult,
  SceneTemplatePreview,
} from "../types/scene";

/** 场景 HTTP 请求层（SRP：纯请求与查询构建，不含业务编排）。 */

interface ListResult<T> {
  items: T[];
  total?: number;
}

const buildSceneQuery = (filters: SceneFilters) => {
  const query = new URLSearchParams({ enabled: filters.enabled });

  if (filters.keyword.trim()) query.set("keyword", filters.keyword.trim());
  if (filters.triggerType) query.set("trigger_type", filters.triggerType);
  return query.toString();
};

const buildTemplateQuery = (keyword: string, category: string) => {
  const query = new URLSearchParams({ limit: "20" });
  if (keyword.trim()) query.set("keyword", keyword.trim());
  if (category && category !== "全部") query.set("category", category);
  return query.toString();
};

export const fetchScenes = async (filters: SceneFilters): Promise<Scene[]> => {
  const result = await apiRequest<ListResult<Scene>>(
    `/api/scenes?${buildSceneQuery(filters)}`,
  );
  return result.items;
};

export const fetchSceneSummary = () =>
  apiRequest<SceneSummary>("/api/scenes/summary");

export const createScene = (payload: SceneInput) =>
  apiRequest<Scene>("/api/scenes", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const saveSceneDraft = (payload: SceneInput) =>
  apiRequest<{ draftId: string; updatedAt: string }>("/api/scenes/drafts", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateSceneEnabled = async (
  sceneId: string,
  enabled: boolean,
) => {
  const result = await apiRequest<Pick<Scene, "id" | "enabled" | "updatedAt">>(
    `/api/scenes/${sceneId}/enabled`,
    { method: "PATCH", body: JSON.stringify({ enabled }) },
  );
  return result;
};

export const executeScene = (sceneId: string, confirmHighRisk: boolean) =>
  apiRequest<SceneExecution>(`/api/scenes/${sceneId}/execute`, {
    method: "POST",
    body: JSON.stringify({ confirmHighRisk, source: "manual" }),
  });

export const copyScene = (sceneId: string, name: string) =>
  apiRequest<Scene>(`/api/scenes/${sceneId}/copy`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });

export const fetchSceneTemplates = async (
  keyword = "",
  category = "",
): Promise<SceneTemplate[]> => {
  const result = await apiRequest<ListResult<SceneTemplate>>(
    `/api/scenes/templates?${buildTemplateQuery(keyword, category)}`,
  );
  return result.items;
};

export const previewSceneTemplate = (templateId: string) =>
  apiRequest<SceneTemplatePreview>(`/api/scenes/templates/${templateId}/preview`);

export const useSceneTemplate = (
  templateId: string,
  payload: SceneTemplateUseInput,
) =>
  apiRequest<Scene>(`/api/scenes/templates/${templateId}/use`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

// ── 场景更新与排序 ──────────────────────────────────────────────────────────────

export const updateScene = (sceneId: string, payload: SceneInput) =>
  apiRequest<Scene>(`/api/scenes/${sceneId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const updateSceneOrder = (items: SceneOrderItem[]) =>
  apiRequest<SceneOrderResult>(`/api/scenes/order`, {
    method: "PATCH",
    body: JSON.stringify({ items }),
  });

// ── 场景执行查询 ────────────────────────────────────────────────────────────────

export const getSceneLogs = async (sceneId: string, limit = 20) => {
  const result = await apiRequest<SceneLogListResponse>(
    `/api/scenes/${sceneId}/logs?limit=${limit}`,
  );
  return result.items;
};

export const getSceneExecution = (executionId: string) =>
  apiRequest<SceneExecution>(`/api/scenes/executions/${executionId}`);

// ── 场景预览与批量操作 ──────────────────────────────────────────────────────────

export const previewScene = (sceneId: string, source = "manual") =>
  apiRequest<ScenePreview>(`/api/scenes/${sceneId}/preview`, {
    method: "POST",
    body: JSON.stringify({ source }),
  });

export const batchUpdateSceneEnabled = (payload: SceneBatchEnabledInput) =>
  apiRequest<SceneBatchEnabledResult>(`/api/scenes/batch/enabled`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const batchUpdateSceneSchedule = (payload: SceneBatchScheduleInput) =>
  apiRequest<SceneBatchScheduleResult>(`/api/scenes/batch/schedule`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
