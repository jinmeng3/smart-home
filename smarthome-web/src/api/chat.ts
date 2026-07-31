import { apiRequest, createApiHeaders, parseResponse } from "./client";
import type { ChatMessage, RecentConversation } from "../types/chat";

export interface ChatCompletionMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface StreamPayload {
  error?: unknown;
  choices?: Array<{
    delta?: {
      content?: string;
    };
  }>;
}

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

const toChatMessage = (message: ChatMessageRead): ChatMessage => ({
  id: String(message.id),
  role: message.role,
  content: message.content,
  timestamp: formatConversationTime(message.created_at),
});

const toRecentConversation = (
  session: ChatSessionRead,
): RecentConversation => ({
  id: String(session.id),
  title: session.title,
  time: formatConversationTime(session.updated_at || session.created_at),
  icon: "MessageCircle",
});

const parseContentDelta = (line: string) => {
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

export const streamChatCompletion = async (
  messages: ChatCompletionMessage[],
  sessionId: string | null,
  onDelta: (content: string) => void,
  signal: AbortSignal,
) => {
  const response = await fetch("/api/chat/completions", {
    method: "POST",
    headers: createApiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ messages, session_id: sessionId, stream: true }),
    signal,
  });

  if (!response.ok || !response.body) {
    await parseResponse<never>(response);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const delta = parseContentDelta(line.trim());

        if (delta) {
          onDelta(delta);
        }
      }
    }

    const delta = parseContentDelta(buffer.trim());

    if (delta) {
      onDelta(delta);
    }
  } finally {
    if (signal.aborted) {
      await reader.cancel().catch(() => undefined);
    }
    reader.releaseLock();
  }
};
