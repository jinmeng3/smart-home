import { computed, shallowRef, ref } from "vue";
import { defineStore } from "pinia";
import {
  useBatchedDeviceUpdates,
  type DeviceUpdate,
} from "../composables/useBatchedDeviceUpdates";
import { useCollapsePhase } from "../composables/useCollapsePhase";
import { useHomeChat } from "../composables/useHomeChat";
import { listDevices as apiListDevices } from "../api/device";
import { mapDashboardDevice } from "../utils/device";
import type { LoadingState } from "../types/loading";

import type { Automation, DashboardDevice } from "../types/device";

/* === 统一 AI 生命周期状态 === */
export type ChatPhase =
    | "idle"
    | "waiting"
    | "executing"
    | "streaming"
    | "awaiting_approval"
    | "completed"
    | "failed";

const buildDeviceMap = (devices: DashboardDevice[]) => ({
  ids: devices.map((device) => device.id),
  byId: devices.reduce<Record<string, DashboardDevice>>((record, device) => {
    record[device.id] = device;
    return record;
  }, {}),
});

export const useHomeStore = defineStore("home", () => {
  const activeMenu = ref("智能对话");
  const selectedDeviceId = ref<string | null>(null);
  const deviceDrawerOpen = ref(false);
  const { ids: initialIds, byId: initialById } = buildDeviceMap([]);
  const deviceIds = shallowRef(initialIds);
  const devicesById = shallowRef<Record<string, DashboardDevice>>(initialById);
  const automations = shallowRef<Automation[]>([]);
  const energyToday = ref(18.62);
  const devicesLoading = ref<LoadingState>("idle");
  const securityAlertHandled = ref(false);

  /* === 左侧导航栏折叠状态 + 三阶段动画（localStorage 持久化） === */
  const {
    collapsed: sidebarCollapsed,
    phase: sidebarPhase,
    toggle: toggleSidebar,
    skipAnimation: skipSidebarAnimation,
  } = useCollapsePhase(
    localStorage.getItem("orion.sidebar-collapsed") === "true",
    (value) => {
      localStorage.setItem("orion.sidebar-collapsed", String(value));
    },
  );

  // 首次加载不播放动画
  skipSidebarAnimation();

  const chat = useHomeChat([]);

  const devices = computed(() => {
    const ids = deviceIds.value;
    const byId = devicesById.value;
    const result: DashboardDevice[] = [];

    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      if (id) {
        const device = byId[id];
        if (device) {
          result.push(device);
        }
      }
    }

    return result;
  });
  const selectedDevice = computed(() =>
    selectedDeviceId.value
      ? (devicesById.value[selectedDeviceId.value] ?? null)
      : null,
  );
  const deviceSummary = computed(() => {
    const ids = deviceIds.value;
    const byId = devicesById.value;
    let online = 0;

    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      if (id && byId[id]?.online) online++;
    }

    return {
      online,
      offline: ids.length - online,
      total: ids.length,
    };
  });
  const hasWarning = computed(
    () => deviceSummary.value.offline > 0 || !securityAlertHandled.value,
  );
  const enabledAutomationCount = computed(() => {
    const items = automations.value;
    let count = 0;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item?.enabled) count++;
    }
    return count;
  });
  const alertCount = computed(() => (securityAlertHandled.value ? 0 : 1));

  const setActiveMenu = (menu: string) => {
    activeMenu.value = menu;
  };

  const loadDevices = async () => {
    devicesLoading.value = "loading";

    try {
      const response = await apiListDevices({
        page: 1,
        pageSize: 20,
        keyword: "",
        type: "",
        status: "",
        room: "",
      });
      const nextDevices = response.items.map(mapDashboardDevice);
      const { ids: nextIds, byId: nextById } = buildDeviceMap(nextDevices);

      deviceIds.value = nextIds;
      devicesById.value = nextById;
      devicesLoading.value = "success";
    } catch {
      // API 加载失败时使用空数据
      deviceIds.value = [];
      devicesById.value = {};
      devicesLoading.value = "error";
    }
  };

  const selectDevice = (device: DashboardDevice) => {
    selectedDeviceId.value = device.id;
    deviceDrawerOpen.value = true;
  };

  const closeDeviceDrawer = () => {
    deviceDrawerOpen.value = false;
  };

  const toggleAutomation = (id: string) => {
    const index = automations.value.findIndex((item) => item.id === id);

    if (index !== -1) {
      const next = automations.value.slice();
      const item = next[index];
      if (item) {
        next[index] = { ...item, enabled: !item.enabled };
        automations.value = next;
      }
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

  const markAlertHandled = () => {
    securityAlertHandled.value = true;
  };

  /* === 统一 AI 生命周期状态 === */
  const chatPhase = computed<ChatPhase>(() => {
    const status = chat.agentStatus.value;
    if (status === "idle") return "idle";
    if (status === "executing") {
      if (chat.eventReceived.value) return "streaming";
      if (chat.executionSteps.value.length > 0) return "executing";
      return "waiting";
    }
    if (status === "awaiting_approval") return "awaiting_approval";
    if (status === "success") return "completed";
    if (status === "error") return "failed";
    return "idle";
  });

  return {
    activeMenu,
    activeSessionId: chat.activeSessionId,
    activeModel: chat.activeModel,
    agentStatus: chat.agentStatus,
    alertCount,
    availableModels: chat.availableModels,
    automations,
    chatPhase,
    closeDeviceDrawer,
    deviceDrawerOpen,
    deviceIds,
    devicesLoading,
    devices,
    devicesById,
    deviceSummary,
    enabledAutomationCount,
    energyToday,
    eventReceived: chat.eventReceived,
    executionSteps: chat.executionSteps,
    fetchModels: chat.fetchModels,
    hasWarning,
    loadConversation: chat.loadConversation,
    deleteConversation: chat.deleteConversation,
    loadDevices,
    markAlertHandled,
    messages: chat.messages,
    agentMode: chat.agentMode,
    pendingApproval: chat.pendingApproval,
    handleDecision: chat.handleDecision,
    decisionSubmitting: chat.decisionSubmitting,
    hasMoreMessages: chat.hasMoreMessages,
    loadEarlierMessages: chat.loadEarlierMessages,
    pendingStatus: chat.pendingStatus,
    queueDeviceUpdate,
    queueDeviceUpdates,
    recentConversations: chat.recentConversations,
    regenerateMessage: chat.regenerateMessage,
    refreshRecentConversations: chat.refreshRecentConversations,
    securityAlertHandled,
    selectedDevice,
    selectDevice,
    sendMessage: chat.sendMessage,
    selectModel: chat.selectModel,
    setActiveMenu,
    sidebarCollapsed,
    sidebarPhase,
    startNewConversation: chat.startNewConversation,
    stopGenerating: chat.stopGenerating,
    toggleAutomation,
    toggleSidebar,
  };
});
