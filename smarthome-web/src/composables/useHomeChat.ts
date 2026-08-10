import { onScopeDispose, ref } from "vue";
import {
  createChatSession as apiCreateChatSession,
  listChatMessages as apiListChatMessages,
  listChatSessions as apiListChatSessions,
  streamChatCompletion as apiStreamChatCompletion,
  type ChatCompletionMessage,
} from "../api/chat";
import { listAIModels, type AIModelRead } from "../api/aiModel";
import type { AgentExecutionStep, AgentStatus } from "../types/chat";
import type { ChatMessage, RecentConversation } from "../types/chat";

const maxMessages = 100;

const createMessageId = () =>
  `message-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const timeFormatter = new Intl.DateTimeFormat("zh-CN", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const currentTime = () => timeFormatter.format(new Date());

const createWelcomeMessage = (): ChatMessage => ({
  id: createMessageId(),
  role: "assistant",
  content: "你好，我是 Orion Home。有什么可以帮你的？",
  timestamp: currentTime(),
});

const createExecutionSteps = (): AgentExecutionStep[] => [
  { id: "understand", label: "正在理解指令", status: "pending" },
  { id: "query", label: "正在请求模型", status: "pending" },
  { id: "execute", label: "正在生成回复", status: "pending" },
  { id: "verify", label: "正在整理结果", status: "pending" },
];

export const useHomeChat = (initialMessages: ChatMessage[]) => {
  const messages = ref<ChatMessage[]>(initialMessages);
  const recentConversations = ref<RecentConversation[]>([]);
  const activeSessionId = ref<string | null>(null);
  const activeModel = ref<string | null>(null);
  const availableModels = ref<AIModelRead[]>([]);
  const agentStatus = ref<AgentStatus>("idle");
  const executionSteps = ref<AgentExecutionStep[]>(createExecutionSteps());
  let replyTimerIds: number[] = [];
  let chatController: AbortController | null = null;
  let streamFrameId = 0;
  let pendingContent = "";

  const clearReplyTimers = () => {
    replyTimerIds.forEach((id) => window.clearTimeout(id));
    replyTimerIds = [];
  };

  const resetExecutionSteps = () => {
    executionSteps.value = createExecutionSteps();
  };

  const cancelStreamFrame = () => {
    if (streamFrameId) {
      window.cancelAnimationFrame(streamFrameId);
      streamFrameId = 0;
    }
    pendingContent = "";
  };

  const stopGenerating = () => {
    chatController?.abort();
    chatController = null;
    cancelStreamFrame();
    clearReplyTimers();
    agentStatus.value = "idle";
    resetExecutionSteps();
  };

  const trimMessages = () => {
    const overflow = messages.value.length - maxMessages;

    if (overflow > 0) {
      messages.value.splice(0, overflow);
    }
  };

  const finishAiReply = () => {
    executionSteps.value = Array.from(executionSteps.value, (step) => ({ ...step, status: "completed" }));
    agentStatus.value = "success";
    replyTimerIds.push(
      window.setTimeout(() => {
        agentStatus.value = "idle";
        resetExecutionSteps();
      }, 700),
    );
  };

  const refreshRecentConversations = async () => {
    try {
      recentConversations.value = await apiListChatSessions();
    } catch {
      recentConversations.value = [];
    }
  };

  const fetchModels = async () => {
    try {
      const models = await listAIModels();
      availableModels.value = models;
      if (!activeModel.value && models.length > 0) {
        const first = models[0];
        if (first) {
          activeModel.value = first.name;
        }
      }
    } catch {
      availableModels.value = [];
    }
  };

  const startNewConversation = async () => {
    stopGenerating();
    messages.value = [createWelcomeMessage()];
    activeSessionId.value = null;

    try {
      const conversation = await apiCreateChatSession();
      activeSessionId.value = conversation.id;
      recentConversations.value = [
        conversation,
        ...recentConversations.value.filter(
          (item) => item.id !== conversation.id,
        ),
      ];
    } catch {
      void refreshRecentConversations();
    }
  };

  const loadConversation = async (sessionId: string) => {
    stopGenerating();
    activeSessionId.value = sessionId;

    try {
      messages.value = await apiListChatMessages(sessionId);
    } catch {
      messages.value = [];
    }
  };

  const runAgentFlow = async () => {
    stopGenerating();
    agentStatus.value = "executing";
    executionSteps.value = createExecutionSteps().map((step, index) => ({
      ...step,
      status: index === 0 ? "completed" : index === 1 ? "executing" : "pending",
    }));

    const assistantMessage: ChatMessage = {
      id: createMessageId(),
      role: "assistant",
      content: "",
      timestamp: currentTime(),
    };
    messages.value.push(assistantMessage);
    trimMessages();
    const assistantMessageIndex = messages.value.length - 1;
    const controller = new AbortController();
    chatController = controller;
    let streamStarted = false;

    const flushContent = () => {
      streamFrameId = 0;
      const currentMessage = messages.value[assistantMessageIndex];

      if (!currentMessage || !pendingContent) {
        return;
      }

      messages.value[assistantMessageIndex] = {
        ...currentMessage,
        content: currentMessage.content + pendingContent,
      };
      pendingContent = "";
    };

    const queueContent = (delta: string) => {
      pendingContent += delta;

      if (!streamFrameId) {
        streamFrameId = window.requestAnimationFrame(flushContent);
      }
    };

    try {
      const allMessages = messages.value;
      const contextMessages: ChatCompletionMessage[] = [];
      for (let i = allMessages.length - 1, count = 0; i >= 0 && count < 12; i--) {
        const msg = allMessages[i];
        if (msg && msg.content.trim()) {
          contextMessages.unshift({ role: msg.role, content: msg.content });
          count++;
        }
      }

      await apiStreamChatCompletion(
        contextMessages,
        activeSessionId.value,
        activeModel.value,
        (delta) => {
          queueContent(delta);
          if (!streamStarted) {
            streamStarted = true;
            agentStatus.value = "executing";
            executionSteps.value = executionSteps.value.map((step, index) => ({
              ...step,
              status:
                index < 2 ? "completed" : index === 2 ? "executing" : "pending",
            }));
          }
        },
        controller.signal,
      );

      if (streamFrameId) {
        window.cancelAnimationFrame(streamFrameId);
        streamFrameId = 0;
      }
      flushContent();

      if (!messages.value[assistantMessageIndex]?.content.trim()) {
        messages.value[assistantMessageIndex] = {
          ...assistantMessage,
          content: "模型没有返回内容。",
        };
      }

      finishAiReply();
      void refreshRecentConversations();
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }

      messages.value[assistantMessageIndex] = {
        ...assistantMessage,
        content: error instanceof Error ? error.message : "请求大模型失败",
      };
      agentStatus.value = "idle";
      resetExecutionSteps();
    } finally {
      if (chatController === controller) {
        chatController = null;
        cancelStreamFrame();
      }
    }
  };

  const sendMessage = (content: string) => {
    const trimmedContent = content.trim();

    if (!trimmedContent) {
      return;
    }

    stopGenerating();
    messages.value.push({
      id: createMessageId(),
      role: "user",
      content: trimmedContent,
      timestamp: currentTime(),
    });
    trimMessages();
    void runAgentFlow();
  };

  onScopeDispose(stopGenerating);

  return {
    activeSessionId,
    activeModel,
    agentStatus,
    availableModels,
    executionSteps,
    fetchModels,
    loadConversation,
    messages,
    recentConversations,
    refreshRecentConversations,
    sendMessage,
    startNewConversation,
    stopGenerating,
  };
};
