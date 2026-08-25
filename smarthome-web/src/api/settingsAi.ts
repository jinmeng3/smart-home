import { apiRequest } from "./client";
import type { SettingsSectionId, SettingsSuggestionItem } from "../types/settings";

/** 后端 AI 建议接口的 DTO，与 settings_suggestions.py 对齐。 */
interface AiSuggestionItemRead {
  id: string;
  target: SettingsSectionId;
  title: string;
  description: string;
}

interface AiSuggestionsRead {
  suggestions: AiSuggestionItemRead[];
  cached: boolean;
}

/**
 * 调用后端 LLM 生成"未完成"设置建议。
 * - force=true 时绕过 5 分钟内存缓存。
 * - 后端 400 表示未配置激活模型；502 表示 LLM 调用失败。
 *   调用方应捕获异常并降级为本地规则匹配结果。
 */
export const fetchAiSuggestions = async (
  snapshot: Record<string, unknown>,
  options: { force?: boolean; signal?: AbortSignal } = {},
): Promise<SettingsSuggestionItem[]> => {
  const params = new URLSearchParams();
  if (options.force) params.set("force", "true");
  const qs = params.toString();
  const url = `/api/settings/suggestions/ai${qs ? `?${qs}` : ""}`;

  const data = await apiRequest<AiSuggestionsRead>(url, {
    method: "POST",
    body: JSON.stringify({ snapshot }),
    signal: options.signal,
  });

  return data.suggestions.map((item) => ({
    id: item.id,
    target: item.target,
    title: item.title,
    description: item.description,
  }));
};
