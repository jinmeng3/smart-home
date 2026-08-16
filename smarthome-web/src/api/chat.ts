import { apiRequest, streamRequest } from "./client";
import type { ChatMessage, RecentConversation } from "../types/chat";
import type { AgentRunRequest } from "../types/chat";
import type { AgentEvent, AgentDecisionRequest, PendingApproval } from "../types/chat";

// === DTO 类型 ===

interface ChatSessionRead {
  id: number;
  title: string;
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
  choices?: Array<{
    delta?: { content?: string };
  }>;
}

export interface ChatCompletionMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface OpenAICompletionsPayload {
  model?: string | null;
  messages: ChatCompletionMessage[];
  sessionId?: number | null;
  stream?: boolean;
  [key: string]: unknown;
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

// === 统一流式请求（SSE 读取 + 分片缓冲 + 取消 + 错误解析） ===
// 后端 `/api/chat/completions` 与 `/api/v1/chat/completions` 复用同一处理器，
// 仅路径参数不同，通过 url 参数区分。

const streamCompletions = async (
  url: string,
  messages: ChatCompletionMessage[],
  sessionId: string | null,
  model: string | null,
  onDelta: (content: string) => void,
  signal: AbortSignal,
) => {
  await streamRequest(
    url,
    (line) => {
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

export const createChatSession = async () => {
  const session = await apiRequest<ChatSessionRead>("/api/chat/sessions", {
    method: "POST",
  });
  return toRecentConversation(session);
};

export const listChatMessages = async (sessionId: string) => {
  const messages = await apiRequest<ChatMessageRead[]>(
    `/api/chat/sessions/${sessionId}/messages`,
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
) =>
  streamCompletions("/api/chat/completions", messages, sessionId, model, onDelta, signal);

// === OpenAI 兼容接口 ===

const openAICompletions = (payload: OpenAICompletionsPayload) =>
  apiRequest<unknown>("/api/v1/chat/completions", {
    method: "POST",
    body: JSON.stringify({
      model: (payload.model as string | null) ?? null,
      messages: payload.messages as ChatCompletionMessage[],
      session_id: (payload.sessionId as number | null) ?? null,
      stream: (payload.stream as boolean) ?? false,
    }),
  });

/** 流式 OpenAI 兼容聊天（/api/v1/chat/completions）。 */
export const streamOpenAICompletions = (
  payload: Omit<OpenAICompletionsPayload, "stream">,
  onDelta: (content: string) => void,
  signal: AbortSignal,
) =>
  streamCompletions(
    "/api/v1/chat/completions",
    payload.messages as ChatCompletionMessage[],
    (payload.sessionId as string | null) ?? null,
    (payload.model as string | null) ?? null,
    onDelta,
    signal,
  );

// === Agent SSE 运行 ===
// 解析一行 SSE 数据，返回 { event, data } 或 null
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
            // 忽略解析失败的行
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