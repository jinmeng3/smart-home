import { apiRequest, streamRequest } from "./client";
import type { ChatMessage, RecentConversation } from "../types/chat";
import type { AgentRunRequest } from "../types/chat";
import type { AgentEvent, AgentDecisionRequest, PendingApproval } from "../types/chat";

// === DTO 类型 ===

interface ChatSessionRead {
  id: number;
  title: string;
  mode: string;
  model_name: string | null;
  created_at: string;
  updated_at: string;
}

interface ChatMessageRead {
  id: number;
  session_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

interface StreamPayload {
  error?: unknown;
  message_id?: number;
  choices?: Array<{
    delta?: { content?: string };
  }>;
}

export interface ChatCompletionMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
}

// === 映射函数 ===

const formatConversationTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(date);
};

const toChatMessage = (message: ChatMessageRead): ChatMessage => ({
  id: String(message.id),
  role: message.role,
  content: message.content,
  timestamp: formatConversationTime(message.created_at),
});

const toRecentConversation = (session: ChatSessionRead): RecentConversation => ({
  id: String(session.id),
  title: session.title,
  time: formatConversationTime(session.updated_at || session.created_at),
  icon: "MessageCircle",
  updatedAt: session.updated_at || session.created_at,
  mode: session.mode === "chat" ? "chat" : "agent",
  modelName: session.model_name ?? null,
});

// === SSE 流式解析 ===

const parseContentDelta = (line: string) => {
  if (!line.startsWith("data: ")) return "";
  const data = line.slice(6).trim();
  if (!data || data === "[DONE]") return "";
  const payload = JSON.parse(data) as StreamPayload;
  if (payload.error) throw new Error(String(payload.error));
  return payload.choices?.[0]?.delta?.content ?? "";
};

const parseMessageId = (line: string): number | null => {
  if (!line.startsWith("data: ")) return null;
  const data = line.slice(6).trim();
  if (!data || data === "[DONE]") return null;
  try {
    const payload = JSON.parse(data) as StreamPayload;
    return typeof payload.message_id === "number" ? payload.message_id : null;
  } catch {
    return null;
  }
};

// === 统一流式请求（SSE 读取 + 分片缓冲 + 取消 + 错误解析） ===

const streamCompletions = async (
  url: string,
  messages: ChatCompletionMessage[],
  sessionId: string | null,
  model: string | null,
  onDelta: (content: string) => void,
  signal: AbortSignal,
  onMessageId?: (messageId: number) => void,
) => {
  await streamRequest(
    url,
    (line) => {
      const messageId = parseMessageId(line);
      if (messageId !== null) {
        onMessageId?.(messageId);
        return;
      }
      const delta = parseContentDelta(line);
      if (delta) onDelta(delta);
    },
    {
      method: "POST",
      body: JSON.stringify({ messages, session_id: sessionId, model, stream: true }),
    },
    signal,
  );
};

// === API 导出函数 ===

export const listChatSessions = async () => {
  const sessions = await apiRequest<ChatSessionRead[]>("/api/chat/sessions");
  return sessions.map(toRecentConversation);
};

export const createChatSession = async (
  mode: "agent" | "chat" = "agent",
  modelName: string | null = null,
) => {
  const params = new URLSearchParams();
  params.set("mode", mode);
  if (modelName) params.set("model_name", modelName);
  const session = await apiRequest<ChatSessionRead>(
    `/api/chat/sessions?${params.toString()}`,
    {
      method: "POST",
    },
  );
  return toRecentConversation(session);
};

/** 更新指定会话的模式（agent / chat）。 */
export const updateChatSessionMode = async (
  sessionId: string,
  mode: "agent" | "chat",
) => {
  const session = await apiRequest<ChatSessionRead>(
    `/api/chat/sessions/${sessionId}/mode`,
    {
      method: "PATCH",
      body: JSON.stringify({ mode }),
    },
  );
  return toRecentConversation(session);
};

/** 更新指定会话使用的模型名。 */
export const updateChatSessionModel = async (
  sessionId: string,
  modelName: string,
) => {
  const session = await apiRequest<ChatSessionRead>(
    `/api/chat/sessions/${sessionId}/model`,
    {
      method: "PATCH",
      body: JSON.stringify({ model_name: modelName }),
    },
  );
  return toRecentConversation(session);
};

export const listChatMessages = async (
  sessionId: string,
  params: { page?: number; page_size?: number } = {},
) => {
  const query = new URLSearchParams();
  if (params.page !== undefined) query.set("page", String(params.page));
  if (params.page_size !== undefined) query.set("page_size", String(params.page_size));
  const qs = query.toString();
  const messages = await apiRequest<ChatMessageRead[]>(
    `/api/chat/sessions/${sessionId}/messages${qs ? `?${qs}` : ""}`,
  );
  return messages.map(toChatMessage);
};

export const deleteChatSession = async (sessionId: string) => {
  await apiRequest<void>(`/api/chat/sessions/${sessionId}`, {
    method: "DELETE",
  });
};

/** 流式聊天补全（/api/chat/completions）。 */
export const streamChatCompletion = (
  messages: ChatCompletionMessage[],
  sessionId: string | null,
  model: string | null,
  onDelta: (content: string) => void,
  signal: AbortSignal,
  onMessageId?: (messageId: number) => void,
) =>
  streamCompletions(
    "/api/chat/completions",
    messages,
    sessionId,
    model,
    onDelta,
    signal,
    onMessageId,
  );

/** 重新生成对话模式的指定助手回复（/api/chat/sessions/{id}/regenerate）。 */
export const regenerateChatCompletion = (
  sessionId: string,
  targetMessageId: number,
  model: string | null,
  onDelta: (content: string) => void,
  signal: AbortSignal,
  onMessageId?: (messageId: number) => void,
): Promise<void> =>
  streamRequest(
    `/api/chat/sessions/${sessionId}/regenerate`,
    (line) => {
      const messageId = parseMessageId(line);
      if (messageId !== null) {
        onMessageId?.(messageId);
        return;
      }
      const delta = parseContentDelta(line);
      if (delta) onDelta(delta);
    },
    {
      method: "POST",
      body: JSON.stringify({
        target_message_id: targetMessageId,
        model,
        stream: true,
      }),
    },
    signal,
  );

// === Agent SSE 运行 ===
function parseSseLine(line: string): { event: string; data: string } | null {
  if (line.startsWith("event: ")) {
    return { event: line.slice(7).trim(), data: "" };
  }
  if (line.startsWith("data: ")) {
    return { event: "", data: line.slice(6).trim() };
  }
  return null;
}

interface SseBuffer {
  event: string;
  data: string;
}

/**
 * 调用后端 Agent SSE 端点，逐事件回调。
 * 参数 onEvent 接收已解析的 AgentEvent 对象。
 */
export const runAgent = async (
  payload: AgentRunRequest,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> => {
  await streamAgentEvents(
    "/api/agent/runs",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    onEvent,
    signal,
  );
};

/**
 * 提交 agent 决策（approve / reject），返回 SSE 事件流。
 */
export const decideAgentOperation = (
  sessionId: number,
  payload: AgentDecisionRequest,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> =>
  streamAgentEvents(
    `/api/agent/sessions/${sessionId}/decisions`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    onEvent,
    signal,
  );

/**
 * 查询当前会话的待确认操作。
 */
export const getPendingAgentOperation = (
  sessionId: number,
  householdId: number,
): Promise<PendingApproval | null> =>
  apiRequest<PendingApproval | null>(
    `/api/agent/sessions/${sessionId}/pending?household_id=${householdId}`,
  );

/**
 * 取消当前会话的待审批操作（删除 checkpoint 中的 pending_approval）。
 *
 * 后端语义：
 *  - 仅在存在 pending 时成功，否则 409
 *  - 取消后服务器会记录审计，后端将 checkpoint 清理
 *  - 与 `decideAgentOperation({ decision: "reject" })` 不同：reject 走完整 Agent
 *    流程记录拒绝事件，cancel 仅清理状态
 */
export const cancelPendingAgentOperation = (
  sessionId: number,
  householdId: number,
  approvalId: string,
): Promise<{ status: "cancelled" }> =>
  apiRequest<{ status: "cancelled" }>(
    `/api/agent/sessions/${sessionId}/cancel-pending?household_id=${householdId}&approval_id=${encodeURIComponent(approvalId)}`,
    { method: "POST" },
  );

/** 会话最近一次 run 的状态与阶段。 */
export interface AgentRunStatus {
  status: string | null;
  phase: string | null;
}

/**
 * 查询会话最近一次 run 的状态与阶段（/api/agent/sessions/{id}/run-status）。
 */
export const getAgentRunStatus = (sessionId: number): Promise<AgentRunStatus> =>
  apiRequest<AgentRunStatus>(`/api/agent/sessions/${sessionId}/run-status`);

/**
 * 重新生成 Agent 模式的指定助手回复（/api/agent/sessions/{id}/regenerate）。
 */
export const regenerateAgentMessage = (
  sessionId: number,
  payload: {
    target_message_id: number;
    model: string | null;
    household_id: number;
  },
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> =>
  streamAgentEvents(
    `/api/agent/sessions/${sessionId}/regenerate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    onEvent,
    signal,
  );

// === 内部工具函数 ===

async function streamAgentEvents(
  url: string,
  init: RequestInit,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  let buffer: SseBuffer = { event: "", data: "" };

  await streamRequest(
    url,
    (line) => {
      if (!line) {
        if (buffer.data) {
          try {
            const parsed = JSON.parse(buffer.data) as AgentEvent;
            parsed.event = (
              buffer.event || parsed.event
            ) as AgentEvent["event"];
            onEvent(parsed);
          } catch {
          }
        }
        buffer = { event: "", data: "" };
        return;
      }

      const parsed = parseSseLine(line);
      if (!parsed) return;

      if (parsed.event) {
        buffer.event = parsed.event;
      }
      if (parsed.data) {
        buffer.data = parsed.data;
      }
    },
    init,
    signal,
  );
}