import { computed, onScopeDispose, ref, shallowRef } from "vue";
import { defineStore } from "pinia";
import { streamChatCompletion } from "../api/chat";
import { useSettingsStore } from "./settings";
import {
  useBatchedDeviceUpdates,
  type DeviceUpdate,
} from "../composables/useBatchedDeviceUpdates";
import {
  automations as mockAutomations,
  devices as mockDevices,
  messages as mockMessages,
  recentConversations,
} from "../mock/home";
import type { AgentExecutionStep, AgentStatus } from "../types/animation";
import type { Automation } from "../types/automation";
import type { ChatMessage } from "../types/chat";
import type { Device } from "../types/device";

const createMessageId = () =>
  `message-${Date.now()}-${Math.random().toString(16).slice(2)}`;
const maxMessages = 100;
const currentTime = () =>
  new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date());

const createExecutionSteps = (): AgentExecutionStep[] => [
  { id: "understand", label: "正在理解指令", status: "pending" },
  { id: "query", label: "正在请求模型", status: "pending" },
  { id: "execute", label: "正在生成回复", status: "pending" },
  { id: "verify", label: "正在整理结果", status: "pending" },
];

export const useHomeStore = defineStore("home", () => {
  const activeMenu = ref("智能对话");
  const settingsStore = useSettingsStore();
  const sidebarCollapsed = computed(
    () => settingsStore.settings.appearance.sidebarCollapsed,
  );
  const selectedDeviceId = ref<string | null>(null);
  const deviceDrawerOpen = ref(false);
  const deviceIds = shallowRef(mockDevices.map((device) => device.id));
  const devicesById = shallowRef<Record<string, Device>>(
    mockDevices.reduce<Record<string, Device>>((record, device) => {
      record[device.id] = device;
      return record;
    }, {}),
  );
  const automations = ref<Automation[]>(mockAutomations);
  const messages = ref<ChatMessage[]>(mockMessages);
  const agentStatus = ref<AgentStatus>("idle");
  const executionSteps = ref<AgentExecutionStep[]>(createExecutionSteps());
  const energyToday = ref(18.62);
  const securityAlertHandled = ref(false);
  let replyTimerIds: number[] = [];
  let chatController: AbortController | null = null;
  let streamFrameId = 0;
  let pendingContent = "";

  const devices = computed(() =>
    deviceIds.value
      .map((id) => devicesById.value[id])
      .filter((device): device is Device => Boolean(device)),
  );
  const selectedDevice = computed(() =>
    selectedDeviceId.value
      ? (devicesById.value[selectedDeviceId.value] ?? null)
      : null,
  );
  const deviceSummary = computed(() => {
    const online = devices.value.filter((device) => device.online).length;

    return {
      online,
      offline: devices.value.length - online,
      total: devices.value.length,
    };
  });
  const hasWarning = computed(
    () => deviceSummary.value.offline > 0 || !securityAlertHandled.value,
  );
  const enabledAutomationCount = computed(
    () => automations.value.filter((automation) => automation.enabled).length,
  );
  const alertCount = computed(() => (securityAlertHandled.value ? 0 : 1));

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

  const setActiveMenu = (menu: string) => {
    activeMenu.value = menu;
  };

  const toggleSidebar = () => {
    settingsStore.settings.appearance.sidebarCollapsed =
      !settingsStore.settings.appearance.sidebarCollapsed;
  };

  const trimMessages = () => {
    const overflow = messages.value.length - maxMessages;
    if (overflow > 0) {
      messages.value.splice(0, overflow);
    }
  };

  const selectDevice = (device: Device) => {
    selectedDeviceId.value = device.id;
    deviceDrawerOpen.value = true;
  };

  const closeDeviceDrawer = () => {
    deviceDrawerOpen.value = false;
  };

  const toggleAutomation = (id: string) => {
    const automation = automations.value.find((item) => item.id === id);

    if (automation) {
      automation.enabled = !automation.enabled;
    }
  };

  const commitDeviceUpdates = (updates: DeviceUpdate[]) => {
    const nextDevicesById = { ...devicesById.value };

    updates.forEach((update) => {
      const currentDevice = nextDevicesById[update.id];

      if (!currentDevice) {
        return;
      }

      nextDevicesById[update.id] = {
        ...currentDevice,
        status: update.status ?? currentDevice.status,
        value:
          update.value === undefined
            ? currentDevice.value
            : String(update.value),
        updatedAt: update.updatedAt ?? currentDevice.updatedAt,
        online: update.online ?? currentDevice.online,
      };
    });

    devicesById.value = nextDevicesById;
  };

  const { queueDeviceUpdate, queueDeviceUpdates } = useBatchedDeviceUpdates(
    commitDeviceUpdates,
    (id) => devicesById.value[id],
  );

  const finishAiReply = () => {
    executionSteps.value = executionSteps.value.map((step) => ({
      ...step,
      status: "completed",
    }));
    agentStatus.value = "success";
    replyTimerIds.push(
      window.setTimeout(() => {
        agentStatus.value = "idle";
        resetExecutionSteps();
      }, 700),
    );
  };

  const runAgentFlow = async () => {
    stopGenerating();
    agentStatus.value = "thinking";
    executionSteps.value = createExecutionSteps().map((step, index) => ({
      ...step,
      status: index === 0 ? "executing" : "pending",
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
      await streamChatCompletion(
        messages.value
          .filter((message) => message.content.trim())
          .slice(-12)
          .map((message) => ({ role: message.role, content: message.content })),
        (delta) => {
          queueContent(delta);
          if (!streamStarted) {
            streamStarted = true;
            agentStatus.value = "executing";
            executionSteps.value = executionSteps.value.map((step) => ({
              ...step,
              status: "completed",
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

  const markAlertHandled = () => {
    securityAlertHandled.value = true;
  };

  onScopeDispose(stopGenerating);

  return {
    activeMenu,
    alertCount,
    agentStatus,
    automations,
    closeDeviceDrawer,
    deviceDrawerOpen,
    deviceIds,
    devices,
    devicesById,
    deviceSummary,
    enabledAutomationCount,
    energyToday,
    executionSteps,
    hasWarning,
    markAlertHandled,
    messages,
    queueDeviceUpdate,
    queueDeviceUpdates,
    recentConversations,
    securityAlertHandled,
    selectedDevice,
    selectDevice,
    sendMessage,
    setActiveMenu,
    sidebarCollapsed,
    stopGenerating,
    toggleAutomation,
    toggleSidebar,
  };
});
