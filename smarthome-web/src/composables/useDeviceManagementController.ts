import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  createDevice as apiCreateDevice,
  deleteDevice as apiDeleteDevice,
  getDevice as apiGetDevice,
  listDeviceLogs as apiListDeviceLogs,
  listDevices as apiListDevices,
  syncDevices as apiSyncDevices,
  updateDevice as apiUpdateDevice,
} from "../api/device";
import { devicePlatformOptions } from "../components/device/deviceMeta";
import type {
  Device,
  DeviceCreatePayload,
  DeviceDetail,
  DeviceFilters,
} from "../types/device";

export type DeviceSortKey = "updated" | "name" | "status";
export type DeviceQuickActionKey = "scan" | "group" | "firmware" | "logs";

const quickActionMessages: Record<Exclude<DeviceQuickActionKey, "logs">, string> = {
  scan: "扫描新设备接口已预留",
  group: "批量分组接口已预留",
  firmware: "固件更新接口已预留",
};

const createDefaultFilters = (): DeviceFilters => ({
  page: 1,
  pageSize: 10,
  keyword: "",
  type: "",
  status: "",
  room: "",
});

export const useDeviceManagementController = () => {
  const filters = reactive<DeviceFilters>(createDefaultFilters());
  const devices = ref<Device[]>([]);
  const total = ref(0);
  const loading = ref(false);
  const syncing = ref(false);
  const saving = ref(false);
  const deleting = ref(false);
  const selectedId = ref<number | null>(null);
  const selectedDevice = ref<DeviceDetail | null>(null);
  const editorOpen = ref(false);
  const editingDevice = ref<Device | null>(null);
  const deleteDialogOpen = ref(false);
  const deletingDevice = ref<Device | null>(null);
  const sort = ref<DeviceSortKey>("updated");

  const viewMode = ref<"all" | "frequent" | "favorite">("all");

  const setViewMode = (mode: "all" | "frequent" | "favorite") => {
    viewMode.value = mode;
  };

  // Favorite device IDs stored in localStorage
  const favoriteDeviceIds = ref<number[]>([]);

  const loadFavorites = () => {
    try {
      const stored = localStorage.getItem("device-favorites");
      if (stored) {
        favoriteDeviceIds.value = JSON.parse(stored);
      }
    } catch {
      favoriteDeviceIds.value = [];
    }
  };

  const saveFavorites = () => {
    localStorage.setItem("device-favorites", JSON.stringify(favoriteDeviceIds.value));
  };

  const toggleFavorite = (deviceId: number) => {
    const index = favoriteDeviceIds.value.indexOf(deviceId);
    if (index > -1) {
      favoriteDeviceIds.value.splice(index, 1);
    } else {
      favoriteDeviceIds.value.push(deviceId);
    }
    saveFavorites();
  };

  const isFavorite = (deviceId: number) => favoriteDeviceIds.value.includes(deviceId);

  // Load favorites on initialization
  loadFavorites();

  const rooms = computed(() =>
    Array.from(new Set(devices.value.map((device) => device.room))).filter(Boolean),
  );

  const filteredDevices = computed(() => {
    let result = devices.value;
    if (viewMode.value === "favorite") {
      result = result.filter((d) => isFavorite(d.id));
    }
    // For "frequent", we could add a heuristic later; for now show all
    return result;
  });

  const sortedDevices = computed(() => {
    let result = filteredDevices.value;
    if (sort.value === "name") {
      return [...result].sort((first, second) =>
        first.name.localeCompare(second.name, "zh-CN"),
      );
    }

    if (sort.value === "status") {
      return [...result].sort((first, second) =>
        first.status.localeCompare(second.status),
      );
    }

    return result;
  });

  const stats = computed(() => {
    let online = 0;
    let offline = 0;
    let warning = 0;
    const items = devices.value;
    for (let i = 0; i < items.length; i++) {
      const device = items[i];
      if (!device) continue;
      if (device.status === "online") online++;
      else if (device.status === "offline") offline++;
      else if (device.status === "warning") warning++;
    }
    return { online, offline, warning, monthlyNew: items.length };
  });

  const platforms = computed(() =>
    devicePlatformOptions.map((name) => {
      const connected = devices.value.some(
        (device) => device.connection === name,
      );

      return {
        name,
        connected,
        status: connected ? "已连接" : "未连接",
      };
    }),
  );

  const loadSelectedDevice = async () => {
    if (selectedId.value === null) {
      selectedDevice.value = null;
      return;
    }

    try {
      selectedDevice.value = await apiGetDevice(selectedId.value);
    } catch (error) {
      selectedDevice.value = null;
      ElMessage.error(
        error instanceof Error ? error.message : "设备详情加载失败",
      );
    }
  };

  const loadDevices = async () => {
    loading.value = true;

    try {
      const response = await apiListDevices(filters);
      devices.value = response.items;
      total.value = response.total;

      const selectedExists = response.items.some(
        (device) => device.id === selectedId.value,
      );
      selectedId.value = selectedExists
        ? selectedId.value
        : (response.items[0]?.id ?? null);
      await loadSelectedDevice();
    } catch (error) {
      devices.value = [];
      total.value = 0;
      ElMessage.error(
        error instanceof Error ? error.message : "设备列表加载失败",
      );
    } finally {
      loading.value = false;
    }
  };

  const updateFilter = <K extends keyof DeviceFilters>(
    key: K,
    value: DeviceFilters[K],
  ) => {
    filters[key] = value;
    if (key !== "page") {
      filters.page = 1;
    }
  };

  const updatePage = (value: number) => {
    filters.page = value;
  };

  const updatePageSize = (value: number) => {
    filters.pageSize = value;
    filters.page = 1;
  };

  const selectDevice = (device: Device) => {
    selectedId.value = device.id;
    void loadSelectedDevice();
  };

  const addDevice = () => {
    editingDevice.value = null;
    editorOpen.value = true;
  };

  const editDevice = (device: Device) => {
    selectedId.value = device.id;
    editingDevice.value = device;
    editorOpen.value = true;
  };

  const saveDevice = async (payload: DeviceCreatePayload) => {
    saving.value = true;

    try {
      if (editingDevice.value) {
        await apiUpdateDevice(editingDevice.value.id, payload);
        ElMessage.success("设备已更新");
      } else {
        const created = await apiCreateDevice(payload);
        selectedId.value = created.id;
        ElMessage.success("设备已添加");
      }

      editorOpen.value = false;
      await loadDevices();
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : "设备保存失败");
    } finally {
      saving.value = false;
    }
  };

  const removeDevice = (device: Device) => {
    deletingDevice.value = device;
    deleteDialogOpen.value = true;
  };

  const cancelRemoveDevice = () => {
    if (deleting.value) {
      return;
    }

    deleteDialogOpen.value = false;
    deletingDevice.value = null;
  };

  const confirmRemoveDevice = async () => {
    if (!deletingDevice.value) {
      return;
    }

    const device = deletingDevice.value;
    deleting.value = true;

    try {
      await apiDeleteDevice(device.id);
      ElMessage.success("设备已删除");
      deleteDialogOpen.value = false;
      deletingDevice.value = null;
      await loadDevices();
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : "设备删除失败");
    } finally {
      deleting.value = false;
    }
  };

  const runSync = async () => {
    syncing.value = true;

    try {
      const response = await apiSyncDevices("Home Assistant");
      ElMessage.success(`同步完成，更新 ${response.synced_count} 台设备`);
      await loadDevices();
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : "设备同步失败");
    } finally {
      syncing.value = false;
    }
  };

  const runBatch = () => {
    ElMessage.info("批量操作接口已预留");
  };

  const runQuickAction = (key: DeviceQuickActionKey) => {
    if (key === "logs") {
      if (selectedId.value === null) {
        ElMessage.warning("请先选择设备");
        return;
      }

      void apiListDeviceLogs(selectedId.value)
        .then((logs) => {
          const latest = logs[0];
          ElMessage.info(
            latest
              ? `共 ${logs.length} 条日志，最近：${latest.message}`
              : "该设备暂无日志",
          );
        })
        .catch((error: unknown) => {
          ElMessage.error(
            error instanceof Error ? error.message : "日志加载失败",
          );
        });
      return;
    }

    ElMessage.info(quickActionMessages[key]);
  };

  return {
    addDevice,
    cancelRemoveDevice,
    confirmRemoveDevice,
    deleteDialogOpen,
    deleting,
    deletingDevice,
    devices,
    editingDevice,
    editorOpen,
    filters,
    loading,
    platforms,
    removeDevice,
    rooms,
    runBatch,
    runQuickAction,
    runSync,
    saveDevice,
    saving,
    selectDevice,
    selectedDevice,
    selectedId,
    sort,
    sortedDevices,
    stats,
    syncing,
    total,
    updateFilter,
    updatePage,
    updatePageSize,
    editDevice,
    loadDevices,
    viewMode,
    setViewMode,
    toggleFavorite,
    isFavorite,
    favoriteDeviceIds,
  };
};
