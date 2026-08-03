import { apiRequest, createApiHeaders, parseResponse } from "./client";
import {
  parseContentDelta,
  toChatMessage,
  toRecentConversation,
  type ChatMessageRead,
  type ChatSessionRead,
} from "./chat/mappers";
import type { ChatMessage, RecentConversation } from "../types/chat";

export interface ChatCompletionMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

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
