import { apiRequest, streamRequest } from "./client";
import type { ChatMessage, RecentConversation } from "../types/chat";

// ── DTO 类型 ──────────────────────────────────────────────────────────────────────

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

// ── 映射函数 ──────────────────────────────────────────────────────────────────────

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
});

// ── SSE 流式解析 ──────────────────────────────────────────────────────────────────

const parseContentDelta = (line: string) => {
  if (!line.startsWith("data: ")) return "";
  const data = line.slice(6).trim();
  if (!data || data === "[DONE]") return "";
  const payload = JSON.parse(data) as StreamPayload;
  if (payload.error) throw new Error(String(payload.error));
  return payload.choices?.[0]?.delta?.content ?? "";
};

// ── 统一流式请求（SSE 读取 + 分片缓冲 + 取消 + 错误解析）──────────────────────────
// 后端 `/api/chat/completions` 与 `/api/v1/chat/completions` 复用同一处理器，
// 仅路径参数不同，通过 url 参数区分。

const streamCompletions = async (
  url: string,
  messages: ChatCompletionMessage[],
  sessionId: string | null,
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
      body: JSON.stringify({ messages, session_id: sessionId, stream: true }),
    },
    signal,
  );
};

// ── API 导出函数 ────────────────────────────────────────────────────────────────────

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

/** 流式聊天补全（/api/chat/completions）。 */
export const streamChatCompletion = (
  messages: ChatCompletionMessage[],
  sessionId: string | null,
  onDelta: (content: string) => void,
  signal: AbortSignal,
) =>
  streamCompletions("/api/chat/completions", messages, sessionId, onDelta, signal);

// ── OpenAI 兼容接口 ────────────────────────────────────────────────────────────────

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
const streamOpenAICompletions = (
  payload: Omit<OpenAICompletionsPayload, "stream">,
  onDelta: (content: string) => void,
  signal: AbortSignal,
) =>
  streamCompletions(
    "/api/v1/chat/completions",
    payload.messages as ChatCompletionMessage[],
    (payload.sessionId as string | null) ?? null,
    onDelta,
    signal,
  );