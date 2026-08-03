import { computed, ref, shallowRef } from "vue";
import { defineStore } from "pinia";
import { useSettingsStore } from "./settings";
import {
  useBatchedDeviceUpdates,
  type DeviceUpdate,
} from "../composables/useBatchedDeviceUpdates";
import { useHomeChat } from "../composables/useHomeChat";
import { deviceService } from "../services/device";
import { mapDashboardDevice } from "../utils/device";
import {
  automations as mockAutomations,
  devices as mockDevices,
  messages as mockMessages,
} from "../mock/home";
import type { Automation } from "../types/automation";
import type { DashboardDevice } from "../types/device";

export const useHomeStore = defineStore("home", () => {
  const activeMenu = ref("智能对话");
  const settingsStore = useSettingsStore();
  const sidebarCollapsed = computed(
    () => settingsStore.settings.appearance.sidebarCollapsed,
  );
  const selectedDeviceId = ref<string | null>(null);
  const deviceDrawerOpen = ref(false);
  const deviceIds = shallowRef(mockDevices.map((device) => device.id));
  const devicesById = shallowRef<Record<string, DashboardDevice>>(
    mockDevices.reduce<Record<string, DashboardDevice>>((record, device) => {
      record[device.id] = device;
      return record;
    }, {}),
  );
  const automations = ref<Automation[]>(mockAutomations);
  const energyToday = ref(18.62);
  const devicesLoading = ref(false);
  const securityAlertHandled = ref(false);
  const chat = useHomeChat(mockMessages);

  const devices = computed(() =>
    deviceIds.value
      .map((id) => devicesById.value[id])
      .filter((device): device is DashboardDevice => Boolean(device)),
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

  const setActiveMenu = (menu: string) => {
    activeMenu.value = menu;
  };

  const toggleSidebar = () => {
    settingsStore.settings.appearance.sidebarCollapsed =
      !settingsStore.settings.appearance.sidebarCollapsed;
  };

  const loadDevices = async () => {
    devicesLoading.value = true;

    try {
      const response = await deviceService.list({
        page: 1,
        pageSize: 20,
        keyword: "",
        type: "",
        status: "",
        room: "",
      });
      const nextDevices = response.items.map(mapDashboardDevice);

      deviceIds.value = nextDevices.map((device) => device.id);
      devicesById.value = nextDevices.reduce<Record<string, DashboardDevice>>(
        (record, device) => {
          record[device.id] = device;
          return record;
        },
        {},
      );
    } catch {
      deviceIds.value = mockDevices.map((device) => device.id);
      devicesById.value = mockDevices.reduce<Record<string, DashboardDevice>>(
        (record, device) => {
          record[device.id] = device;
          return record;
        },
        {},
      );
    } finally {
      devicesLoading.value = false;
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

  const markAlertHandled = () => {
    securityAlertHandled.value = true;
  };

  return {
    activeMenu,
    activeSessionId: chat.activeSessionId,
    alertCount,
    agentStatus: chat.agentStatus,
    automations,
    closeDeviceDrawer,
    deviceDrawerOpen,
    deviceIds,
    devicesLoading,
    devices,
    devicesById,
    deviceSummary,
    enabledAutomationCount,
    energyToday,
    executionSteps: chat.executionSteps,
    hasWarning,
    loadConversation: chat.loadConversation,
    loadDevices,
    markAlertHandled,
    messages: chat.messages,
    queueDeviceUpdate,
    queueDeviceUpdates,
    recentConversations: chat.recentConversations,
    refreshRecentConversations: chat.refreshRecentConversations,
    securityAlertHandled,
    selectedDevice,
    selectDevice,
    sendMessage: chat.sendMessage,
    setActiveMenu,
    startNewConversation: chat.startNewConversation,
    sidebarCollapsed,
    stopGenerating: chat.stopGenerating,
    toggleAutomation,
    toggleSidebar,
  };
});
