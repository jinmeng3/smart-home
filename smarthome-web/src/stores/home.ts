import { computed, shallowRef, ref } from "vue";
import { defineStore } from "pinia";
import {
  useBatchedDeviceUpdates,
  type DeviceUpdate,
} from "../composables/useBatchedDeviceUpdates";
import { useHomeChat } from "../composables/useHomeChat";
import { listDevices as apiListDevices } from "../api/device";
import { mapDashboardDevice } from "../utils/device";
import type { LoadingState } from "../types/loading";

import type { Automation, DashboardDevice } from "../types/device";

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
    stopGenerating: chat.stopGenerating,
    toggleAutomation,
  };
});
