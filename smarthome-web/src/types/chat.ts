export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface RecentConversation {
  id: string;
  title: string;
  time: string;
  icon: string;
  /** 原始更新时间（ISO），用于按 今天/昨天/更早 分组 */
  updatedAt: string;
  /** 会话模式：agent / chat */
  mode: "agent" | "chat";
  /** 会话使用的模型名 */
  modelName?: string | null;
}

export type AgentStatus =
  "idle" | "thinking" | "executing" | "awaiting_approval" | "success" | "error";

export type SuggestionStatus = "pending" | "executing" | "completed" | "failed";

export interface AgentExecutionStep {
  id: string;
  label: string;
  status: SuggestionStatus;
  message?: string;
}

// === Agent 工具名 → 友好中文标签 ===
// 流式步骤列表 / 状态面板展示工具调用时，用中文代替原始 snake_case 名，
// 避免“正在调用 detect_automation_conflicts”这类长英文名过长且不友好。
export const TOOL_LABELS: Record<string, string> = {
  list_rooms: "列出房间",
  get_room: "查询房间",
  list_devices: "列出设备",
  get_device: "查询设备",
  list_scenes: "列出场景",
  get_scene: "查询场景",
  list_automations: "列出自动化",
  get_automation: "查询自动化",
  list_device_logs: "查询设备日志",
  list_scene_executions: "查询场景执行记录",
  list_automation_executions: "查询自动化执行记录",
  preview_scene: "预览场景",
  preview_automation_change: "预览自动化变更",
  detect_automation_conflicts: "检测自动化冲突",
  inspect_household_health: "全屋健康巡检",
  execute_scene: "执行场景",
  create_automation: "创建自动化",
  update_automation: "更新自动化",
  set_automation_enabled: "启停自动化",
  delete_automation: "删除自动化",
  set_device_power: "开关设备电源",
  set_device_temperature: "设置空调温度",
  set_curtain_position: "设置窗帘开合",
};

/** 把后端下发的 snake_case 工具名转换为友好中文标签；未收录时回退为原名。 */
export function friendlyToolLabel(tool: string): string {
  return TOOL_LABELS[tool] || tool;
}

// === Agent SSE 事件类型 ===

export interface AgentEventBase {
  event_id: string;
  run_id: string;
  event: string;
}

export interface RunStartedEvent extends AgentEventBase {
  event: "run_started";
  session_id: number;
  household_id: number;
}

export interface MessageDeltaEvent extends AgentEventBase {
  event: "message_delta";
  content: string;
}

export interface ToolStartedEvent extends AgentEventBase {
  event: "tool_started";
  call_id: string;
  tool: string;
  summary: string;
}

export interface ToolCompletedEvent extends AgentEventBase {
  event: "tool_completed";
  call_id: string;
  tool: string;
  result: string;
}

export interface ToolFailedEvent extends AgentEventBase {
  event: "tool_failed";
  call_id: string;
  tool: string;
  code: string;
  error: string;
}

export interface RunCompletedEvent extends AgentEventBase {
  event: "run_completed";
  session_id: number;
  status: string;
  message_id?: number | null;
}

export interface AgentErrorEvent extends AgentEventBase {
  event: "error";
  code: string;
  message: string;
  retryable: boolean;
}

export interface ScenePreviewStep {
  step_id: string;
  name: string;
  description: string;
  device_id: string;
  device_name: string | null;
  order: number;
}

// === 审批预览判别联合类型 ===

/** 场景执行预览 */
export interface SceneApprovalPreview {
  kind: "scene_execution";
  scene_id: string;
  scene_name: string;
  enabled: boolean;
  risk_level: string;
  device_count: number;
  summary?: string;
  steps: ScenePreviewStep[];
}

/** 自动化操作预览 */
export interface AutomationApprovalPreview {
  kind: "create_automation" | "update_automation" | "set_automation_enabled" | "delete_automation";
  operation: string;
  automation_id: number | null;
  automation_name?: string;
  risk_level: string;
  summary?: string;
  trigger_count?: number;
  condition_count?: number;
  action_count?: number;
  changed_fields?: string[];
  affected_device_names?: string[];
  target_enabled?: boolean;
}

export type ApprovalPreview = SceneApprovalPreview | AutomationApprovalPreview;

export interface PendingApproval {
  approval_id: string;
  run_id: string;
  session_id: number;
  call_id: string;
  tool: string;
  args: Record<string, unknown>;
  risk_level: "low" | "high" | "unknown";
  reasons: string[];
  preview: Record<string, unknown>;
  resource_version: string;
}

export interface ApprovalRequiredEvent extends AgentEventBase {
  event: "approval_required";
  session_id: number;
  approval_id: string;
  operator: string;
  call_id: string;
  risk_level: "low" | "high" | "unknown";
  reasons: string[];
  preview: Record<string, unknown>;
}

export interface ExecutionStatusEvent extends AgentEventBase {
  event: "execution_status";
  session_id: number;
  operator: string;
  status: "submitted" | "running" | "verified" | "failed" | "unknown";
  call_id: string;
  execution_id: string | null;
  message: string;
}

export type AgentDecision = "approve" | "reject";

export interface AgentDecisionRequest {
  household_id: number;
  approval_id: string;
  decision: AgentDecision;
}

export type AgentEvent =
  | RunStartedEvent
  | MessageDeltaEvent
  | ToolStartedEvent
  | ToolCompletedEvent
  | ToolFailedEvent
  | ApprovalRequiredEvent
  | ExecutionStatusEvent
  | RunCompletedEvent
  | AgentErrorEvent;

// === Agent 运行请求 ===

export interface AgentRunRequest {
  session_id: number;
  household_id: number;
  household_name?: string;
  model?: string | null;
  message: string;
  tools_enabled?: boolean;
}

export interface HouseholdInfo {
  id: number;
  name: string;
}
