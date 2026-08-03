import { apiRequest } from "../api/client";
import type {
    Scene,
    SceneExecution,
    SceneFilters,
    SceneInput,
    SceneSummary,
    SceneTemplate,
    SceneTemplateUseInput,
} from "../types/scene";

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

export const listScenes = async (filters: SceneFilters): Promise<Scene[]> => {
    const result = await apiRequest<ListResult<Scene>>(
        `/api/scenes?${buildSceneQuery(filters)}`,
    );
    return result.items;
};

export const getSceneSummary = () =>
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

export const updateSceneEnabled = async (scene: Scene, enabled: boolean) => {
    const result = await apiRequest<Pick<Scene, "id" | "enabled" | "updatedAt">>(
        `/api/scenes/${scene.id}/enabled`,
        { method: "PATCH", body: JSON.stringify({ enabled }) },
    );
    return { ...scene, ...result };
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

export const listSceneTemplates = async (
    keyword = "",
    category = "",
): Promise<SceneTemplate[]> => {
    const query = new URLSearchParams({ limit: "20" });
    if (keyword.trim()) query.set("keyword", keyword.trim());
    if (category && category !== "全部") query.set("category", category);
    const result = await apiRequest<ListResult<SceneTemplate>>(
        `/api/scenes/templates?${query.toString()}`,
    );
    return result.items;
};

export const useSceneTemplate = (
    templateId: string,
    payload: SceneTemplateUseInput,
) =>
    apiRequest<Scene>(`/api/scenes/templates/${templateId}/use`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
