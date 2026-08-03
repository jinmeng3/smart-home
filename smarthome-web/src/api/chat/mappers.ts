import type { ChatMessage, RecentConversation } from "../../types/chat";

/** 对话 DTO 与领域模型互转、流式响应解析（SRP：映射与解析职责独立于请求）。 */

export interface ChatSessionRead {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageRead {
  id: number;
  session_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

const formatConversationTime = (value: string) => {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
};

export const toChatMessage = (message: ChatMessageRead): ChatMessage => ({
  id: String(message.id),
  role: message.role,
  content: message.content,
  timestamp: formatConversationTime(message.created_at),
});

export const toRecentConversation = (
  session: ChatSessionRead,
): RecentConversation => ({
  id: String(session.id),
  title: session.title,
  time: formatConversationTime(session.updated_at || session.created_at),
  icon: "MessageCircle",
});

export interface StreamPayload {
  error?: unknown;
  choices?: Array<{
    delta?: {
      content?: string;
    };
  }>;
}

export const parseContentDelta = (line: string) => {
  if (!line.startsWith("data: ")) {
    return "";
  }

  const data = line.slice(6).trim();

  if (!data || data === "[DONE]") {
    return "";
  }

  const payload = JSON.parse(data) as StreamPayload;

  if (payload.error) {
    throw new Error(String(payload.error));
  }

  return payload.choices?.[0]?.delta?.content ?? "";
};
