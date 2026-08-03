import {
  copyScene as apiCopyScene,
  createScene as apiCreateScene,
  executeScene as apiExecuteScene,
  fetchSceneSummary,
  fetchSceneTemplates,
  fetchScenes,
  saveSceneDraft as apiSaveSceneDraft,
  updateSceneEnabled as apiUpdateSceneEnabled,
  useSceneTemplate as apiUseSceneTemplate,
} from "../api/scenes";
import type {
  Scene,
  SceneExecution,
  SceneFilters,
  SceneInput,
  SceneSummary,
  SceneTemplate,
  SceneTemplateUseInput,
} from "../types/scene";

/**
 * 场景领域服务层（DIP：store 与组件只依赖此抽象，
 * 不直接依赖 API 实现；单一职责——仅编排场景操作）。
 */
export const listScenes = (filters: SceneFilters): Promise<Scene[]> =>
  fetchScenes(filters);

export const getSceneSummary = (): Promise<SceneSummary> =>
  fetchSceneSummary();

export const createScene = (payload: SceneInput): Promise<Scene> =>
  apiCreateScene(payload);

export const saveSceneDraft = (payload: SceneInput) =>
  apiSaveSceneDraft(payload);

export const updateSceneEnabled = async (
  scene: Pick<Scene, "id">,
  enabled: boolean,
) => {
  const result = await apiUpdateSceneEnabled(scene.id, enabled);
  return { ...scene, ...result };
};

export const executeScene = (
  sceneId: string,
  confirmHighRisk: boolean,
): Promise<SceneExecution> => apiExecuteScene(sceneId, confirmHighRisk);

export const copyScene = (sceneId: string, name: string): Promise<Scene> =>
  apiCopyScene(sceneId, name);

export const listSceneTemplates = (
  keyword = "",
  category = "",
): Promise<SceneTemplate[]> => fetchSceneTemplates(keyword, category);

export const useSceneTemplate = (
  templateId: string,
  payload: SceneTemplateUseInput,
): Promise<Scene> => apiUseSceneTemplate(templateId, payload);
