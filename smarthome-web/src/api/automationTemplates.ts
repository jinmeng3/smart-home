import { apiRequest } from "./client";
import type { DeviceSummary } from "../types/deviceSummary";

/** 与后端 AutomationTemplateItem 对齐。 */
export interface AutomationTemplateItem {
  name: string;
  description: string;
  trigger_type: "schedule" | "location" | "device" | "manual";
  icon: string;
  tone: string;
  device_count: number;
  triggers: Array<{ type: string; config: Record<string, unknown> }>;
  actions: Array<{
    type: "device_command";
    position: number;
    deviceId: number | null;
    config: Record<string, unknown>;
    device_type?: string | null;
    room?: string | null;
  }>;
}

interface AiTemplatesRead {
  templates: AutomationTemplateItem[];
  cached: boolean;
}

/** 调用后端 LLM 生成 N 条自动化模板。force=true 绕过 10 分钟缓存。 */
export const fetchAiAutomationTemplates = async (
  deviceSummary: DeviceSummary,
  count = 6,
  options: { force?: boolean; signal?: AbortSignal } = {},
): Promise<AutomationTemplateItem[]> => {
  const data = await apiRequest<AiTemplatesRead>("/api/automations/templates/ai", {
    method: "POST",
    body: JSON.stringify({
      device_summary: deviceSummary,
      count,
      force: options.force ?? false,
    }),
    signal: options.signal,
  });
  return data.templates;
};
