// === 流控件项目 ===
// 触发器 / 条件 / 动作均以 { type, config } 作为基础；
// 条件额外 carry position；动作额外 carry position 与 target。

export interface FlowItem {
  type: string;
  config: Record<string, unknown>;
}

export interface ConditionWrite extends FlowItem {
  position?: number | null;
}

export interface ActionWrite extends FlowItem {
  position: number;
  deviceId?: number | null;
  sceneId?: string | null;
}

// === 自动化规则 CRUD ===

export interface AutomationCreate {
  name: string;
  description?: string;
  enabled?: boolean;
  triggers: FlowItem[];
  conditions?: ConditionWrite[];
  actions: ActionWrite[];
  priority?: number;
  cooldownSeconds?: number;
  delaySeconds?: number;
  note?: string;
}

export interface AutomationUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  triggers?: FlowItem[];
  conditions?: ConditionWrite[];
  actions?: ActionWrite[];
  priority?: number;
  cooldownSeconds?: number;
  delaySeconds?: number;
  note?: string;
  version?: number;
}

/** 自动化规则详情 (GET /api/automations/{id}) */
export interface AutomationRule {
  id: number;
  householdId: number;
  name: string;
  description: string;
  triggerType: string;
  enabled: boolean;
  deviceCount: number;
  priority: number;
  cooldownSeconds: number;
  delaySeconds: number;
  note: string;
  version: number;
  triggers: FlowItem[];
  conditions: ConditionWrite[];
  actions: ActionWrite[];
  createdAt: string;
  updatedAt: string;
}

// === 列表 ===

export interface AutomationSummary {
  enabled: number;
  total: number;
  running: number;
  executionsToday: number;
  abnormal: number;
}

export interface AutomationListItem {
  id: number;
  name: string;
  description: string;
  triggerType: string;
  enabled: boolean;
  deviceCount: number;
  updatedAt: string;
}

export interface AutomationListResponse {
  summary: AutomationSummary;
  items: AutomationListItem[];
  total: number;
}

// === 启用 / 停用 ===

export interface EnabledRead {
  id: number;
  enabled: boolean;
}

// === 执行与记录 ===

export interface ExecuteRead {
  executionId: number;
  status: string;
}

export interface ExecutionRecord {
  id: number;
  status: string;
  source: string;
  triggerSnapshot: Record<string, unknown>;
  durationMs: number | null;
  errorMessage: string | null;
  startedAt: string;
  finishedAt: string | null;
}

export interface ExecutionListRead {
  total: number;
  items: ExecutionRecord[];
}

// === 批量操作 ===

export interface BatchEnableRead {
  updatedCount: number;
  unchangedCount: number;
  executionBatchId: string | null;
}

export interface BatchScheduleWrite {
  ruleIds: number[];
  timezone: string;
  time: string;
  weekdays: number[];
  frequency: "daily" | "weekly";
  interval?: number;
}
