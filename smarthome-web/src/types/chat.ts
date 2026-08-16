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

export interface SceneApprovalPreview {
  scene_id: string;
  scene_name: string;
  enabled: boolean;
  risk_level: "low" | "high" | "unknown";
  device_count: number;
  steps: ScenePreviewStep[];
}

export interface PendingApproval {
  approval_id: string;
  run_id: string;
  session_id: number;
  call_id: string;
  tool: string;
  args: Record<string, unknown>;
  risk_level: "low" | "high" | "unknown";
  reasons: string[];
  preview: SceneApprovalPreview;
  resource_version: string;
}

export interface ApprovalRequiredEvent extends AgentEventBase {
  event: "approval_required";
  session_id: number;
  approval_id: string;
  operator: string;
  risk_level: "low" | "high" | "unknown";
  reasons: string[];
  preview: SceneApprovalPreview;
}

export interface ExecutionStatusEvent extends AgentEventBase {
  event: "execution_status";
  session_id: number;
  operator: string;
  status: "submitted" | "running" | "verified" | "failed" | "unknown";
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
}

export interface HouseholdInfo {
  id: number;
  name: string;
}
