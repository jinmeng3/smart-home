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

/** 单设备命令预览（对应后端 classify_device_operation）。
 *  前端 AgentConfirmationCard 据此路由到“设备命令”分支。*/
export interface DeviceCommandApprovalPreview {
  kind: "device_command";
  operation: string;       // set_device_power / set_device_temperature / set_curtain_position
  device_id: number;
  device_name: string;
  device_brand?: string;
  device_type: string;     // light / air_conditioner / socket / curtain / ...
  risk_level: string;
  /** 通用影响描述（不固定设备/操作）。 */
  impact: string;
  summary?: string;
  // 操作参数（可选）
  power?: "on" | "off";
  temperature?: number;
  mode?: string;
  position?: number;
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

export type ApprovalPreview =
  | SceneApprovalPreview
  | AutomationApprovalPreview
  | DeviceCommandApprovalPreview;

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
