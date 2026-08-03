import {
  createChatSession,
  listChatMessages,
  listChatSessions,
  streamChatCompletion,
} from "../api/chat";
import type { ChatMessage, RecentConversation } from "../types/chat";

/**
 * 对话领域服务层（DIP：组合式函数只依赖此抽象，
 * 不直接依赖 API 实现；同时保持单一职责——仅编排对话会话）。
 */
export const chatService = {
  listRecentConversations(): Promise<RecentConversation[]> {
    return listChatSessions();
  },

  createSession(): Promise<RecentConversation> {
    return createChatSession();
  },

  loadMessages(sessionId: string): Promise<ChatMessage[]> {
    return listChatMessages(sessionId);
  },

  streamCompletion(
    messages: Array<{ role: "user" | "assistant" | "system"; content: string }>,
    sessionId: string | null,
    onDelta: (content: string) => void,
    signal: AbortSignal,
  ): Promise<void> {
    return streamChatCompletion(messages, sessionId, onDelta, signal);
  },
};
