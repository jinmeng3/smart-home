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
