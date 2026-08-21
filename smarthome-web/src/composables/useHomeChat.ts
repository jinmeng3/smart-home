import { onScopeDispose, ref, watch } from "vue";
import {
  createChatSession as apiCreateChatSession,
  deleteChatSession as apiDeleteChatSession,
  listChatMessages as apiListChatMessages,
  listChatSessions as apiListChatSessions,
  runAgent as apiRunAgent,
  decideAgentOperation as apiDecideAgentOperation,
  getPendingAgentOperation as apiGetPendingAgentOperation,
} from "../api/chat";
import { listAIModels, getAIModel, activateAIModel, type AIModelRead } from "../api/aiModel";
import { useHouseholdStore } from "../stores/households";
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
  ApprovalRequiredEvent,
  ExecutionStatusEvent,
  HouseholdInfo,
  PendingApproval,
} from "../types/chat";
import type { ChatMessage, RecentConversation } from "../types/chat";

/** 根据 pending approval 的 tool 和 preview.kind 生成友好的待确认状态文案 */
const pendingApprovalLabel = (approval: PendingApproval): string => {
  const kind = String(approval.preview?.kind || "");
  const tool = approval.tool;
  if (kind === "scene_execution") return "等待用户确认场景执行";
  if (kind === "create_automation") return "等待用户确认创建自动化";
  if (kind === "update_automation") return "等待用户确认修改自动化";
  if (kind === "set_automation_enabled") return "等待用户确认启停自动化";
  if (kind === "delete_automation") return "等待用户确认删除自动化";
  if (tool) return `等待用户确认 ${tool}`;
  return "等待用户确认操作";
};

const maxMessages = 100;
const pageSize = 50;

const createMessageId = () =>
  `message-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const timeFormatter = new Intl.DateTimeFormat("zh-CN", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const currentTime = () => timeFormatter.format(new Date());

/**
 * 将后端错误码映射为面向用户的友好消息。
 * 覆盖：模型错误、工具错误、权限拒绝、限流、预算耗尽、确认超时、用户取消。
 */
const errorCodeMap: Record<string, string> = {
  model_error: "模型调用失败，请检查模型配置或稍后重试",
  tool_error: "工具执行异常，请稍后重试",
  permission_denied: "权限不足，无法执行该操作",
  rate_limited: "请求过于频繁，请稍后重试",
  budget_exhausted: "预算已用尽，请联系管理员",
  timeout: "请求超时，请稍后重试",
  user_cancelled: "用户已取消操作",
  approval_expired: "确认请求已过期，请重新发起",
  approval_consumed: "该确认请求已被处理",
  approval_not_found: "确认请求不存在",
  version_conflict: "版本冲突，请刷新后重试",
};

const getFriendlyError = (code: string, fallback: string): string =>
  errorCodeMap[code] || fallback;

export const useHomeChat = (initialMessages: ChatMessage[]) => {
  const householdStore = useHouseholdStore();
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
  const pendingApproval = ref<PendingApproval | null>(null);
  const decisionSubmitting = ref(false);
  const agentMode = ref<"agent" | "chat">("agent");
  const hasMoreMessages = ref(false);
  const loadedMessagePage = ref(1);
  let replyTimerIds: number[] = [];
  let chatController: AbortController | null = null;
  let streamFrameId = 0;
  let pendingContent = "";
  let streamDrainResolver: (() => void) | null = null;
  let stepIdCounter = 0;
  let activeToolCallId = "";
  let seenEventIds = new Set<string>();

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

  const createContentStreamer = (assistantMessageIndex: number) => {
    const flushContent = () => {
      streamFrameId = 0;
      const currentMessage = messages.value[assistantMessageIndex];
      if (!currentMessage || !pendingContent) {
        streamDrainResolver?.();
        streamDrainResolver = null;
        return;
      }

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

    const waitForContentDrain = () => {
      if (!pendingContent && !streamFrameId) return Promise.resolve();
      return new Promise<void>((resolve) => {
        streamDrainResolver = resolve;
        if (!streamFrameId) {
          streamFrameId = window.requestAnimationFrame(flushContent);
        }
      });
    };

    const queueContent = (delta: string) => {
      pendingContent += delta;
      if (!streamFrameId) {
        streamFrameId = window.requestAnimationFrame(flushContent);
      }
    };

    return { queueContent, waitForContentDrain };
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
  };

  interface EventProcessorOptions {
    assistantMessageIndex: number;
    queueContent: (delta: string) => void;
    onRunCompleted?: (status: string) => void;
    onApprovalReceived?: () => void;
  }

  const createEventProcessor = (options: EventProcessorOptions) => {
    let streamStarted = false;

    const updateStep = (
      id: string,
      label: string,
      status: "executing" | "completed" | "failed",
      message?: string,
    ) => {
      const idx = executionSteps.value.findIndex((s) => s.id === id);
      if (idx !== -1) {
        const updated = [...executionSteps.value];
        const prev = updated[idx]!;
        updated[idx] = {
          id: prev.id,
          label: prev.label,
          status,
          ...(message ? { message } : {}),
        };
        executionSteps.value = updated;
      } else {
        executionSteps.value = [
          ...executionSteps.value,
          { id, label, status, ...(message ? { message } : {}) },
        ];
      }
    };

    return (event: AgentEvent) => {
      if (event.event_id && seenEventIds.has(event.event_id)) {
        return;
      }
      if (event.event_id) {
        seenEventIds.add(event.event_id);
      }

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
          options.queueContent(ev.content);
          break;
        }
        case "tool_started": {
          eventReceived.value = true;
          const ev = event as ToolStartedEvent;
          stepIdCounter++;
          const stepId = ev.call_id || `tool-${stepIdCounter}`;
          activeToolCallId = stepId;
          updateStep(stepId, ev.summary || `正在调用 ${ev.tool}`, "executing");
          break;
        }
        case "tool_completed": {
          const ev = event as ToolCompletedEvent;
          updateStep(ev.call_id || activeToolCallId, `已完成 ${ev.tool}`, "completed");
          break;
        }
        case "tool_failed": {
          const ev = event as ToolFailedEvent;
          updateStep(ev.call_id || activeToolCallId, `${ev.tool} 执行失败`, "failed", ev.error);
          break;
        }
        case "approval_required": {
          eventReceived.value = true;
          const ev = event as ApprovalRequiredEvent;
          pendingApproval.value = {
            approval_id: ev.approval_id,
            run_id: event.run_id,
            session_id: ev.session_id,
            call_id: ev.call_id || "",
            tool: ev.operator || "",
            args: {},
            risk_level: ev.risk_level,
            reasons: ev.reasons,
            preview: ev.preview,
            resource_version: "",
          };
          agentStatus.value = "awaiting_approval";
          pendingStatus.value = "需要确认操作";
          options.onApprovalReceived?.();
          break;
        }
        case "execution_status": {
          const ev = event as ExecutionStatusEvent;
          pendingStatus.value = ev.message || `执行状态：${ev.status}`;
          if (ev.call_id) {
            if (ev.status === "failed") {
              updateStep(ev.call_id, ev.operator, "failed", ev.message);
            } else if (
              ev.status === "verified" ||
              ev.status === "submitted" ||
              ev.status === "running"
            ) {
              updateStep(ev.call_id, ev.operator, "completed");
            }
          }
          break;
        }
        case "run_completed": {
          eventReceived.value = true;
          const ev = event as RunCompletedEvent;
          options.onRunCompleted?.(ev.status);
          break;
        }
        case "error": {
          eventReceived.value = true;
          const ev = event as AgentErrorEvent;
          const friendlyMsg = ev.code
            ? getFriendlyError(ev.code, ev.message || "智能体执行出错")
            : ev.message || "智能体执行出错";
          const currentMessage = messages.value[options.assistantMessageIndex];
          if (currentMessage) {
            messages.value[options.assistantMessageIndex] = {
              ...currentMessage,
              content: friendlyMsg,
            };
          }
          agentStatus.value = "error";
          pendingStatus.value = friendlyMsg;
          updateStep(
            `error-${executionSteps.value.length + 1}`,
            getFriendlyError(ev.code, "智能体执行失败"),
            "failed",
            friendlyMsg,
          );
          break;
        }
      }
    };
  };

  const fetchHousehold = async () => {
    const active = householdStore.activeHousehold;
    household.value = active ? { id: active.id, name: active.name } : null;
  };

  watch(
    () => householdStore.activeHouseholdId,
    () => {
      if (!householdStore.loadedOnce) return;
      stopGenerating();
      pendingApproval.value = null;
      pendingStatus.value = "";
      void fetchHousehold();
      void refreshRecentConversations();
    },
  );

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
    }
  };

  const startNewConversation = async () => {
    stopGenerating();
    messages.value = [];
    activeSessionId.value = null;
    pendingApproval.value = null;
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
    pendingApproval.value = null;
    loadedMessagePage.value = 1;
    hasMoreMessages.value = false;
    await fetchHousehold();

    try {
      const msgs = await apiListChatMessages(sessionId, {
        page: 1,
        page_size: pageSize,
      });
      messages.value = msgs;
      hasMoreMessages.value = msgs.length >= pageSize;
      loadedMessagePage.value = 1;

      if (household.value && sessionId) {
        try {
          const pending = await apiGetPendingAgentOperation(
            Number(sessionId),
            household.value.id,
          );
          if (pending) {
            pendingApproval.value = pending as PendingApproval;
            agentStatus.value = "awaiting_approval";
            pendingStatus.value = pendingApprovalLabel(pending as PendingApproval);
          }
        } catch {
        }
      }
    } catch {
      messages.value = [];
      hasMoreMessages.value = false;
    }
  };

  /** 加载更早的消息（增量加载，避免历史不可达） */
  const loadEarlierMessages = async () => {
    if (!activeSessionId.value || !hasMoreMessages.value) return;
    const nextPage = loadedMessagePage.value + 1;
    try {
      const msgs = await apiListChatMessages(activeSessionId.value, {
        page: nextPage,
        page_size: pageSize,
      });
      if (msgs.length === 0) {
        hasMoreMessages.value = false;
        return;
      }
      messages.value = [...msgs, ...messages.value];
      loadedMessagePage.value = nextPage;
      hasMoreMessages.value = msgs.length >= pageSize;
      if (messages.value.length > maxMessages) {
        messages.value = messages.value.slice(messages.value.length - maxMessages);
      }
    } catch {
    }
  };

  const deleteConversation = async (sessionId: string) => {
    await apiDeleteChatSession(sessionId);
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = null;
      messages.value = [];
      pendingApproval.value = null;
    }
    recentConversations.value = recentConversations.value.filter(
      (item) => item.id !== sessionId,
    );
  };

  const handleDecision = async (decision: "approve" | "reject") => {
    if (decisionSubmitting.value || !pendingApproval.value || !activeSessionId.value) return;
    const hh = household.value;
    const sid = Number(activeSessionId.value);
    if (!hh || !Number.isFinite(sid) || sid <= 0 || !Number.isFinite(hh.id) || hh.id <= 0 || !pendingApproval.value.approval_id) {
      pendingStatus.value = "提交失败：家庭或会话信息不完整，请刷新后重试";
      return;
    }
    decisionSubmitting.value = true;

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
    let runCompleted = false;
    let runFailed = false;

    agentStatus.value = "executing";
    eventReceived.value = false;
    pendingStatus.value =
      decision === "approve" ? "正在执行操作" : "正在处理拒绝";
    resetExecutionSteps();

    const { queueContent, waitForContentDrain } = createContentStreamer(assistantMessageIndex);

    let ended = false;
    const handleEvent = createEventProcessor({
      assistantMessageIndex,
      queueContent,
      onRunCompleted: (status) => {
        ended = true;
        if (status === "completed") {
          runCompleted = true;
        } else if (status === "failed") {
          runFailed = true;
        } else if (status === "pending_confirmation") {
          runCompleted = true;
        }
      },
    });

    try {
      await apiDecideAgentOperation(
        sid,
        {
          household_id: hh!.id,
          approval_id: pendingApproval.value.approval_id,
          decision,
        },
        handleEvent,
        controller.signal,
      );

      await waitForContentDrain();

      if (runFailed) {
        agentStatus.value = "error";
        pendingStatus.value = "操作执行失败";
      } else if (runCompleted) {
        finishAiReply();
      } else if (!ended) {
        try {
          const pending = await apiGetPendingAgentOperation(
            sid,
            hh!.id,
          );
          if (pending) {
            pendingApproval.value = pending as PendingApproval;
            agentStatus.value = "awaiting_approval";
            pendingStatus.value = "已恢复，等待确认操作";
            return;
          }
        } catch {
        }
        finishAiReply();
      }

      pendingApproval.value = null;
      pendingStatus.value =
        decision === "reject" ? "已拒绝操作" : pendingStatus.value;
      void refreshRecentConversations();
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      const errMsg = error instanceof Error ? error.message : "决策提交失败";
      if (error instanceof Error) {
        if (errMsg.includes("expired") || errMsg.includes("过期")) {
          pendingStatus.value = getFriendlyError("approval_expired", "确认请求已过期");
        } else if (errMsg.includes("consumed") || errMsg.includes("已处理")) {
          pendingStatus.value = getFriendlyError("approval_consumed", "该确认请求已被处理");
          pendingApproval.value = null;
        } else if (errMsg.includes("没有待确认操作")) {
          pendingStatus.value = "确认请求已失效，请重新发起";
        } else {
          pendingStatus.value = errMsg;
        }
      } else {
        pendingStatus.value = errMsg;
      }
      if (activeSessionId.value && household.value) {
        try {
          const pending = await apiGetPendingAgentOperation(
            Number(activeSessionId.value),
            household.value.id,
          );
          if (pending) {
            pendingApproval.value = pending as PendingApproval;
            agentStatus.value = "awaiting_approval";
            pendingStatus.value = "连接已恢复，等待确认操作";
          } else {
            pendingApproval.value = null;
            agentStatus.value = "success";
            pendingStatus.value = "操作已执行完成";
          }
        } catch {
        }
      }
    } finally {
      decisionSubmitting.value = false;
      if (chatController === controller) {
        chatController = null;
        cancelStreamFrame();
      }
    }
  };

  const runAgentFlow = async () => {
    stopGenerating();
    pendingApproval.value = null;
    seenEventIds = new Set<string>();

    if (!activeModel.value && availableModels.value.length === 0) {
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === "user") {
        messages.value[messages.value.length - 1] = {
          ...lastMsg,
          content: lastMsg.content + "\n\n（错误：未配置 AI 模型，请先在设置中添加模型）",
        };
      }
      return;
    }

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
    let runCompleted = false;

    const { queueContent, waitForContentDrain } = createContentStreamer(assistantMessageIndex);

    const handleEvent = createEventProcessor({
      assistantMessageIndex,
      queueContent,
      onRunCompleted: (status) => {
        if (status === "completed") {
          runCompleted = true;
        }
      },
    });

    try {
      const sidNum = Number(activeSessionId.value);
      if (!Number.isFinite(sidNum) || sidNum <= 0) {
        throw new Error("会话不存在或尚未创建，请先创建会话后重试");
      }
      await apiRunAgent(
        {
          session_id: sidNum,
          household_id: hh.id,
          household_name: hh.name,
          model: activeModel.value,
          message: messages.value[assistantMessageIndex - 1]?.content || "",
          tools_enabled: agentMode.value === "agent",
        },
        handleEvent,
        controller.signal,
      );

      await waitForContentDrain();

      if (runCompleted && agentStatus.value === "executing") {
        finishAiReply();
        void refreshRecentConversations();
      }

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
      const errMsg = error instanceof Error ? error.message : "请求大模型失败";
      const currentMessage = messages.value[assistantMessageIndex];
      if (currentMessage) {
        messages.value[assistantMessageIndex] = {
          ...currentMessage,
          content: errMsg,
        };
      }
      agentStatus.value = "error";
      pendingStatus.value = errMsg;
      executionSteps.value = [
        ...executionSteps.value,
        {
          id: `error-${executionSteps.value.length + 1}`,
          label: "请求执行失败",
          status: "failed",
          message: errMsg,
        },
      ];
      if (activeSessionId.value && household.value) {
        try {
          const pending = await apiGetPendingAgentOperation(
            Number(activeSessionId.value),
            household.value.id,
          );
          if (pending) {
            pendingApproval.value = pending as PendingApproval;
            agentStatus.value = "awaiting_approval";
            pendingStatus.value = `连接已恢复，${pendingApprovalLabel(pending as PendingApproval)}`;
          }
        } catch {
        }
      }
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
    pendingApproval.value = null;

    if (!activeModel.value && availableModels.value.length === 0) {
      messages.value.push({
        id: createMessageId(),
        role: "assistant",
        content: "请先在设置中添加并启用 AI 模型，然后返回对话。",
        timestamp: currentTime(),
      });
      return;
    }

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

  const setAgentMode = (mode: "agent" | "chat") => {
    agentMode.value = mode;
  };

  onScopeDispose(stopGenerating);

  return {
    activeSessionId,
    activeModel,
    agentStatus,
    availableModels,
    decisionSubmitting,
    eventReceived,
    executionSteps,
    fetchModels,
    handleDecision,
    loadConversation,
    deleteConversation,
    messages,
    pendingApproval,
    pendingStatus,
    recentConversations,
    regenerateMessage,
    refreshRecentConversations,
    sendMessage,
    selectModel,
    agentMode,
    setAgentMode,
    loadEarlierMessages,
    hasMoreMessages,
    startNewConversation,
    stopGenerating,
  };
};