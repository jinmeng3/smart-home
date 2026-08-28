export type SceneTriggerType = "manual" | "schedule" | "location" | "device";

export type SceneStatus = "enabled" | "disabled" | "running" | "failed";

export interface SceneStep {
  id: string;
  name: string;
  description: string;
  deviceId: string;
  order: number;
  action?: StepAction | null;
  actionValue?: number | null;
}

export interface Scene {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  triggerType: SceneTriggerType;
  triggerLabel: string;
  deviceCount: number;
  enabled: boolean;
  recommended: boolean;
  roomLabels?: string[];
  highRisk?: boolean;
  sortOrder?: number;
  sourceTemplateId?: string | null;
  steps: SceneStep[];
  createdAt: string;
  updatedAt: string;
}

export interface SceneFilters {
  keyword: string;
  triggerType: SceneTriggerType | "";
  enabled: "all" | "enabled" | "disabled";
}

export type SceneStepStatus = "pending" | "running" | "completed" | "failed" | "skipped";

/** 场景步骤动作枚举：场景执行时真正下发给设备的写操作。 */
export type StepAction = "on" | "off" | "set_temperature" | "set_position" | "noop";

export interface SceneStepInput {
  name: string;
  description: string;
  deviceId: string;
  order: number;
  /**
   * 动作指令：场景执行时真正下发给设备的写操作。
   * 未填时（undefined）后端会按设备历史动作取反（A3 语义），
   * 详见后端 docs/funnel-routing-architecture.md。
   */
  action?: StepAction | null;
  /** 动作参数：调温 → 目标温度；开合度 → 0-100；开关类 → 不填。 */
  actionValue?: number | null;
}

export interface SceneInput {
  name: string;
  description: string;
  icon: string;
  color: string;
  triggerType: SceneTriggerType;
  triggerLabel: string;
  roomLabels: string[];
  deviceIds: string[];
  enabled: boolean;
  recommended?: boolean;
  highRisk?: boolean;
  steps: SceneStepInput[];
}

export interface SceneTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  triggerType: SceneTriggerType;
  triggerLabel: string;
  roomLabels: string[];
  deviceCount: number;
  recommended: boolean;
  category: string;
  steps: SceneStep[];
}

export interface SceneSummary {
  enabled: number;
  automation: number;
  manual: number;
  monthlyExecutions: number;
  enabledRate: number;
  automationRate: number;
  manualRate: number;
  monthlyGrowthRate: number;
}

export interface SceneExecution {
  executionId: string;
  sceneId: string;
  status: string;
  startedAt: string;
  finishedAt: string | null;
  steps: Array<{ stepId: string; status: string; message: string | null }>;
}

export interface SceneTemplateUseInput {
  name?: string;
  enabled: boolean;
  deviceMapping?: Record<string, string>;
}

// === 场景执行日志 ===

export interface SceneLog {
  id: string;
  sceneId: string;
  status: string;
  source: string;
  startedAt: string;
  finishedAt: string | null;
  message: string | null;
}

export interface SceneLogListResponse {
  items: SceneLog[];
}

// === 场景预览 ===

export interface ScenePreviewStep {
  stepId: string;
  name: string;
  deviceId: string;
  estimatedMs: number;
  riskLevel: "low" | "high";
}

export interface ScenePreview {
  sceneId: string;
  highRisk: boolean;
  triggerLabel: string;
  steps: ScenePreviewStep[];
}

// === 场景排序 ===

export interface SceneOrderItem {
  id: string;
  sort_order: number;
}

export interface SceneOrderResult {
  updated: number;
}

// === 场景批量操作 ===

export interface SceneBatchEnabledInput {
  sceneIds: string[];
  enabled: boolean;
}

export interface SceneBatchEnabledResult {
  updatedCount: number;
}

export interface SceneBatchScheduleInput {
  sceneIds: string[];
  triggerType: SceneTriggerType;
  triggerLabel: string;
}

export interface SceneBatchScheduleResult {
  updatedCount: number;
}

// === 场景模板预览 ===

export interface SceneTemplatePreviewStep {
  name: string;
  description: string;
  deviceId: string;
  matched: boolean;
}

export interface SceneTemplatePreview {
  templateId: string;
  matchedDeviceCount: number;
  missingDeviceCount: number;
  steps: SceneTemplatePreviewStep[];
}
