import { computed, shallowRef, ref, watch } from "vue";
import { defineStore } from "pinia";
import {
  useBatchedDeviceUpdates,
  type DeviceUpdate,
} from "../composables/useBatchedDeviceUpdates";
import { useCollapsePhase } from "../composables/useCollapsePhase";
import { useHomeChat } from "../composables/useHomeChat";
import { listDevices as apiListDevices, getTodayEnergy } from "../api/device";
import { listAutomations, toggleAutomationEnabled } from "../api/automation";
import { getHouseholdOverview } from "../api/overview";
import { useHouseholdStore } from "./households";
import { mapDashboardDevice } from "../utils/device";
import type { LoadingState } from "../types/loading";

import type { Automation, DashboardDevice } from "../types/device";
import type { OverviewAlert } from "../types/overview";

/** 后端 triggerType → 前端展示文字 */
const TRIGGER_LABEL: Record<string, string> = {
  location: "位置触发",
  schedule: "时间触发",
  device: "设备状态",
  manual: "手动触发",
};

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
  const automationsLoading = ref(false);
  const energyToday = ref(18.62);
  const devicesLoading = ref<LoadingState>("idle");
  const securityAlertHandled = ref(false);
  const alerts = shallowRef<OverviewAlert[]>([]);

  const householdStore = useHouseholdStore();

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
    () =>
      deviceSummary.value.offline > 0 ||
      (alerts.value.length > 0 && !securityAlertHandled.value),
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
  const alertCount = computed(() =>
    securityAlertHandled.value ? 0 : alerts.value.length,
  );

  const setActiveMenu = (menu: string) => {
    activeMenu.value = menu;
  };

  const loadTodayEnergy = async () => {
    const householdId = householdStore.activeHouseholdId;
    if (!householdId) {
      energyToday.value = 0;
      return;
    }

    try {
      const result = await getTodayEnergy(householdId);
      energyToday.value = result.energy_kwh;
    } catch {
      // 保留原值，加载失败不阻断页面
    }
  };

  /** 从家庭总览接口拉取真实告警列表，作为 securityAlertHandled/alertCount 的数据源 */
  const loadOverviewAlerts = async (householdId: number) => {
    try {
      const overview = await getHouseholdOverview(householdId);
      const raw = Array.isArray(overview.alerts) ? (overview.alerts as any[]) : [];
      alerts.value = raw.map((alert) => ({
        level: (alert.level || alert.severity || "warning") as string,
        title: (alert.title || alert.message || alert.name || "") as string,
        location: (alert.location || alert.room_name || "") as string,
      }));
    } catch (err) {
      // 加载失败不阻断页面，保留现有告警
      console.error("家庭告警加载失败:", err);
    }
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
      deviceIds.value = [];
      devicesById.value = {};
      devicesLoading.value = "error";
    }
  };

  const loadAutomations = async () => {
    const householdId = householdStore.activeHouseholdId;
    if (!householdId) {
      automations.value = [];
      return;
    }

    automationsLoading.value = true;
    try {
      const result = await listAutomations(householdId, {
        page: 1,
        pageSize: 50,
      });
      const items = result.items.map<Automation>((item) => ({
        id: String(item.id),
        name: item.name,
        trigger: TRIGGER_LABEL[item.triggerType] ?? item.triggerType,
        actions: [],
        enabled: item.enabled,
        time: item.updatedAt || "",
        description: item.description,
      }));
      automations.value = items;
    } catch {
      automations.value = [];
    } finally {
      automationsLoading.value = false;
    }
  };

  /** 切换自动化启停：先本地乐观更新，失败回滚 */
  const toggleAutomation = async (id: string) => {
    const index = automations.value.findIndex((item) => item.id === id);

    if (index === -1) {
      return;
    }

    const next = automations.value.slice();
    const item = next[index];
    if (!item) {
      return;
    }

    const newEnabled = !item.enabled;
    next[index] = { ...item, enabled: newEnabled };
    automations.value = next;

    try {
      await toggleAutomationEnabled(Number(id), newEnabled);
    } catch (cause) {
      // 失败回滚本地状态
      const current = automations.value[index];
      if (current) {
        const rollback = automations.value.slice();
        rollback[index] = { ...current, enabled: !newEnabled };
        automations.value = rollback;
      }
      throw cause;
    }
  };

  // 家庭切换或首次加载时重新加载自动化列表、今日能耗与安防告警
  watch(
    () => householdStore.activeHouseholdId,
    (id) => {
      if (id != null) {
        void loadAutomations().catch(() => undefined);
        void loadTodayEnergy().catch(() => undefined);
        void loadOverviewAlerts(id).catch(() => undefined);
      } else {
        automations.value = [];
        energyToday.value = 0;
        alerts.value = [];
        securityAlertHandled.value = false;
      }
    },
    { immediate: true },
  );

  const selectDevice = (device: DashboardDevice) => {
    selectedDeviceId.value = device.id;
    deviceDrawerOpen.value = true;
  };

  const closeDeviceDrawer = () => {
    deviceDrawerOpen.value = false;
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
    alerts,
    availableModels: chat.availableModels,
    automations,
    automationsLoading,
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
    ensureSession: chat.ensureSession,
    eventReceived: chat.eventReceived,
    executionSteps: chat.executionSteps,
    fetchModels: chat.fetchModels,
    hasWarning,
    loadConversation: chat.loadConversation,
    deleteConversation: chat.deleteConversation,
    loadDevices,
    loadAutomations,
    loadOverviewAlerts,
    loadTodayEnergy,
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
    setAgentMode: chat.setAgentMode,
    setActiveMenu,
    sidebarCollapsed,
    sidebarPhase,
    startNewConversation: chat.startNewConversation,
    stopGenerating: chat.stopGenerating,
    toggleAutomation,
    toggleSidebar,
  };
});
