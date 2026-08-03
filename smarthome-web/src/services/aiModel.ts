import {
  activateAIModel,
  createAIModel,
  getAIModel,
  listAIModels,
  updateAIModel,
  type AIModelRead,
  type AIModelUpdate,
} from "../api/aiModel";

/**
 * AI 模型领域服务层（DIP：store 只依赖此抽象，
 * 不直接依赖 API 实现；单一职责——仅编排模型查询与配置）。
 */
export const aiModelService = {
  getCurrent(): Promise<AIModelRead> {
    return getAIModel();
  },

  list(): Promise<AIModelRead[]> {
    return listAIModels();
  },

  activate(modelId: number): Promise<AIModelRead> {
    return activateAIModel(modelId);
  },

  update(payload: AIModelUpdate): Promise<AIModelRead> {
    return updateAIModel(payload);
  },

  create(
    payload: Required<Pick<AIModelUpdate, "name" | "provider" | "api_endpoint">> &
      AIModelUpdate,
  ): Promise<AIModelRead> {
    return createAIModel(payload);
  },
};
