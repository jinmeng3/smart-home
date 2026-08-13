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
  "idle" | "thinking" | "executing" | "success" | "error";

export type SuggestionStatus = "pending" | "executing" | "completed" | "failed";

export interface AgentExecutionStep {
  id: string;
  label: string;
  status: SuggestionStatus;
  message?: string;
}

// ── Agent SSE 事件类型 ──────────────────────────────────────────────────

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

export type AgentEvent =
  | RunStartedEvent
  | MessageDeltaEvent
  | ToolStartedEvent
  | ToolCompletedEvent
  | ToolFailedEvent
  | RunCompletedEvent
  | AgentErrorEvent;

// ── Agent 运行请求 ───────────────────────────────────────────────────────

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
