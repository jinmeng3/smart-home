import { onScopeDispose, ref } from "vue";
import {
  createChatSession as apiCreateChatSession,
  deleteChatSession as apiDeleteChatSession,
  listChatMessages as apiListChatMessages,
  listChatSessions as apiListChatSessions,
  runAgent as apiRunAgent,
} from "../api/chat";
import { listAIModels, getAIModel, activateAIModel, type AIModelRead } from "../api/aiModel";
import { listHouseholds } from "../api/account";
import type {
  AgentExecutionStep,
  AgentStatus,
  AgentEvent,
  MessageDeltaEvent,
  ToolStartedEvent,
  ToolCompletedEvent,
  ToolFailedEvent,
  AgentErrorEvent,
  RunCompletedEvent,
  HouseholdInfo,
} from "../types/chat";
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

export const useHomeChat = (initialMessages: ChatMessage[]) => {
  const messages = ref<ChatMessage[]>(initialMessages);
  const recentConversations = ref<RecentConversation[]>([]);
  const activeSessionId = ref<string | null>(null);
  const activeModel = ref<string | null>(null);
  const availableModels = ref<AIModelRead[]>([]);
  const agentStatus = ref<AgentStatus>("idle");
  const executionSteps = ref<AgentExecutionStep[]>([]);
  const eventReceived = ref(false);
  const pendingStatus = ref("");
  const household = ref<HouseholdInfo | null>(null);
  let replyTimerIds: number[] = [];
  let chatController: AbortController | null = null;
  let streamFrameId = 0;
  let pendingContent = "";
  let streamDrainResolver: (() => void) | null = null;
  let stepIdCounter = 0;

  const clearReplyTimers = () => {
    replyTimerIds.forEach((id) => window.clearTimeout(id));
    replyTimerIds = [];
  };

  const resetExecutionSteps = () => {
    executionSteps.value = [];
    stepIdCounter = 0;
  };

  const cancelStreamFrame = () => {
    if (streamFrameId) {
      window.cancelAnimationFrame(streamFrameId);
      streamFrameId = 0;
    }
    pendingContent = "";
    streamDrainResolver?.();
    streamDrainResolver = null;
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
    executionSteps.value = executionSteps.value.map((step) => ({
      ...step,
      status: "completed" as const,
    }));
    agentStatus.value = "success";
    replyTimerIds.push(
      window.setTimeout(() => {
        agentStatus.value = "idle";
        resetExecutionSteps();
      }, 700),
    );
  };

  const fetchHousehold = async () => {
    try {
      const list = await listHouseholds();
      if (list.length > 0) {
        const first = list[0];
        if (first) {
          household.value = { id: first.id, name: first.name };
        }
      }
    } catch {
      household.value = null;
    }
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
      // 从后端读取当前激活的模型，作为默认选择
      try {
        const active = await getAIModel();
        activeModel.value = active.name;
      } catch {
        if (models.length > 0) {
          const first = models[0];
          if (first) {
            activeModel.value =
              models.find((m) => m.is_active)?.name ?? first.name;
          }
        }
      }
    } catch {
      availableModels.value = [];
    }
  };

  const selectModel = async (name: string) => {
    const model = availableModels.value.find((m) => m.name === name);
    if (!model) return;
    activeModel.value = name;
    try {
      await activateAIModel(model.id);
    } catch {
      // 激活失败不影响本地选择，运行时会校验
    }
  };

  const startNewConversation = async () => {
    stopGenerating();
    messages.value = [];
    activeSessionId.value = null;
    await fetchHousehold();

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
    await fetchHousehold();

    try {
      messages.value = await apiListChatMessages(sessionId);
    } catch {
      messages.value = [];
    }
  };

  const deleteConversation = async (sessionId: string) => {
    await apiDeleteChatSession(sessionId);
    // 若删除的是当前会话，则回到新会话状态
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = null;
      messages.value = [];
    }
    recentConversations.value = recentConversations.value.filter(
      (item) => item.id !== sessionId,
    );
  };

  const runAgentFlow = async () => {
    stopGenerating();

    if (!household.value) {
      await fetchHousehold();
    }
    const hh = household.value;
    if (!hh) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === "user") {
        messages.value[messages.value.length - 1] = {
          ...lastMsg,
          content: lastMsg.content + "\n\n（错误：未找到家庭信息，请先创建家庭）",
        };
      }
      return;
    }

    agentStatus.value = "executing";
    eventReceived.value = false;
    pendingStatus.value = "正在等待智能体响应";
    resetExecutionSteps();

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
    let runCompleted = false;

    const flushContent = () => {
      streamFrameId = 0;
      const currentMessage = messages.value[assistantMessageIndex];
      if (!currentMessage || !pendingContent) {
        streamDrainResolver?.();
        streamDrainResolver = null;
        return;
      }

      // 部分模型会一次返回完整大段内容。按帧揭示适量字符，既保留
      // 真实 token 流，又避免大块增量瞬间铺满整个回复。
      const chunkSize = Math.min(18, Math.max(4, Math.ceil(pendingContent.length / 24)));
      const visibleChunk = pendingContent.slice(0, chunkSize);
      pendingContent = pendingContent.slice(chunkSize);
      messages.value[assistantMessageIndex] = {
        ...currentMessage,
        content: currentMessage.content + visibleChunk,
      };

      if (pendingContent) {
        streamFrameId = window.requestAnimationFrame(flushContent);
      } else {
        streamDrainResolver?.();
        streamDrainResolver = null;
      }
    };

    const queueContent = (delta: string) => {
      pendingContent += delta;
      if (!streamFrameId) {
        streamFrameId = window.requestAnimationFrame(flushContent);
      }
    };

    const waitForContentDrain = () => {
      if (!pendingContent && !streamFrameId) return Promise.resolve();
      return new Promise<void>((resolve) => {
        streamDrainResolver = resolve;
        if (!streamFrameId) {
          streamFrameId = window.requestAnimationFrame(flushContent);
        }
      });
    };

    // 更新或添加执行步骤
    const updateStep = (id: string, label: string, status: "executing" | "completed" | "failed", message?: string) => {
      const idx = executionSteps.value.findIndex((s) => s.id === id);
      if (idx !== -1) {
        const updated = [...executionSteps.value];
        const prev = updated[idx]!;
        updated[idx] = { id: prev.id, label: prev.label, status, ...(message ? { message } : {}) };
        executionSteps.value = updated;
      } else {
        executionSteps.value = [...executionSteps.value, { id, label, status, message }];
      }
    };

    // 处理 SSE 事件
    const handleEvent = (event: AgentEvent) => {
      if (!streamStarted) {
        streamStarted = true;
      }

      switch (event.event) {
        case "run_started": {
          pendingStatus.value = "已开始运行";
          break;
        }
        case "message_delta": {
          eventReceived.value = true;
          const ev = event as MessageDeltaEvent;
          queueContent(ev.content);
          break;
        }
        case "tool_started": {
          eventReceived.value = true;
          const ev = event as ToolStartedEvent;
          stepIdCounter++;
          const stepId = `tool-${stepIdCounter}`;
          updateStep(stepId, ev.summary || `正在调用 ${ev.tool}`, "executing");
          break;
        }
        case "tool_completed": {
          const ev = event as ToolCompletedEvent;
          updateStep(`tool-${stepIdCounter}`, `已完成 ${ev.tool}`, "completed");
          break;
        }
        case "tool_failed": {
          const ev = event as ToolFailedEvent;
          updateStep(`tool-${stepIdCounter}`, `${ev.tool} 执行失败`, "failed", ev.error);
          break;
        }
        case "run_completed": {
          eventReceived.value = true;
          const ev = event as RunCompletedEvent;
          if (ev.status === "completed") {
            runCompleted = true;
          }
          break;
        }
        case "error": {
          eventReceived.value = true;
          const ev = event as AgentErrorEvent;
          const currentMessage = messages.value[assistantMessageIndex];
          if (currentMessage) {
            messages.value[assistantMessageIndex] = {
              ...currentMessage,
              content: ev.message || "智能体执行出错",
            };
          }
          agentStatus.value = "error";
          break;
        }
      }
    };

    try {
      const sessionId = activeSessionId.value ? Number(activeSessionId.value) : 0;
      await apiRunAgent(
        {
          session_id: sessionId,
          household_id: hh.id,
          household_name: hh.name,
          model: activeModel.value,
          message: messages.value[assistantMessageIndex - 1]?.content || "",
        },
        handleEvent,
        controller.signal,
      );

      await waitForContentDrain();

      if (runCompleted && agentStatus.value === "executing") {
        finishAiReply();
      }

      // 如果 run_completed 没有触发 finishAiReply（例如事件流提前结束）
      if (agentStatus.value === "executing") {
        const currentMessage = messages.value[assistantMessageIndex];
        if (!currentMessage?.content.trim()) {
          messages.value[assistantMessageIndex] = {
            ...assistantMessage,
            content: "模型没有返回内容。",
          };
        }
        finishAiReply();
      }

      void refreshRecentConversations();
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      const currentMessage = messages.value[assistantMessageIndex];
      if (currentMessage) {
        messages.value[assistantMessageIndex] = {
          ...currentMessage,
          content: error instanceof Error ? error.message : "请求大模型失败",
        };
      }
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
    if (!trimmedContent) return;

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

  const regenerateMessage = (assistantMessageId: string) => {
    if (agentStatus.value === "executing") return;

    const assistantIndex = messages.value.findIndex(
      (message) => message.id === assistantMessageId,
    );
    if (assistantIndex < 0 || messages.value[assistantIndex]?.role !== "assistant") {
      return;
    }

    let userIndex = assistantIndex - 1;
    while (userIndex >= 0 && messages.value[userIndex]?.role !== "user") {
      userIndex--;
    }
    if (userIndex < 0) return;

    stopGenerating();
    messages.value.splice(assistantIndex);
    void runAgentFlow();
  };

  onScopeDispose(stopGenerating);

  return {
    activeSessionId,
    activeModel,
    agentStatus,
    availableModels,
    eventReceived,
    executionSteps,
    fetchModels,
    loadConversation,
    deleteConversation,
    messages,
    pendingStatus,
    recentConversations,
    regenerateMessage,
    refreshRecentConversations,
    sendMessage,
    selectModel,
    startNewConversation,
    stopGenerating,
  };
};
