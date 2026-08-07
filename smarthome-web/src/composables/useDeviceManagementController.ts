import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useAsyncAction } from "./useAsyncAction";
import { useDebouncedFilter } from "./useDebouncedFilter";
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
  DeviceLog,
} from "../types/device";

export type DeviceSortKey = "updated" | "name" | "status";
export type DeviceQuickActionKey = "scan" | "delete" | "firmware" | "logs";

const logActionLabels: Record<string, string> = {
  create: "创建",
  update: "更新",
  sync: "同步",
  group: "分组",
  delete: "删除",
  turn_on: "开启",
  turn_off: "关闭",
};

const quickActionMessages: Record<Exclude<DeviceQuickActionKey, "logs">, string> = {
  scan: "扫描新设备接口已预留",
  delete: "批量删除接口已预留",
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
  const selectedId = ref<number | null>(null);
  const selectedDevice = ref<DeviceDetail | null>(null);
  const editorOpen = ref(false);
  const editingDevice = ref<Device | null>(null);
  const deleteDialogOpen = ref(false);
  const deletingDevice = ref<Device | null>(null);
  const batchDeleteDialogOpen = ref(false);
  const batchMode = ref(false);
  const selectedDeviceIds = ref<number[]>([]);
  const batchDeletingIds = ref<number[]>([]);
  const logDialogOpen = ref(false);
  const deviceLogs = ref<DeviceLog[]>([]);
  const logDeviceName = ref("");
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

  const loadDevices = async (signal?: AbortSignal) => {
    loading.value = true;

    try {
      const response = await apiListDevices(filters, signal);
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
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      devices.value = [];
      total.value = 0;
      ElMessage.error(
        error instanceof Error ? error.message : "设备列表加载失败",
      );
    } finally {
      loading.value = false;
    }
  };

  // 筛选输入（搜索/类型/状态/房间）防抖加载：输入停止 250ms 后才请求，
  // 同时用 AbortSignal 取消旧请求，避免快速连续筛选时旧数据覆盖新数据。
  const debouncedLoad = useDebouncedFilter((signal) => loadDevices(signal), 250);
  const loadDevicesDebounced = debouncedLoad.run;
  const cancelDebouncedLoad = debouncedLoad.cancel;

  // ── 设备操作（useAsyncAction：统一 loading / 防重复提交 / 错误提示）─────────────

  const { loading: saving, run: saveDevice } = useAsyncAction(
    async (payload: DeviceCreatePayload) => {
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
    },
    {
      onError: (error) =>
        ElMessage.error(error instanceof Error ? error.message : "设备保存失败"),
    },
  );

  const { loading: deleting, run: confirmRemoveDevice } = useAsyncAction(
    async () => {
      if (!deletingDevice.value) return;
      const device = deletingDevice.value;
      await apiDeleteDevice(device.id);
      ElMessage.success("设备已删除");
      deleteDialogOpen.value = false;
      deletingDevice.value = null;
      await loadDevices();
    },
    {
      onError: (error) =>
        ElMessage.error(error instanceof Error ? error.message : "设备删除失败"),
    },
  );

  const { loading: syncing, run: runSync } = useAsyncAction(
    async () => {
      const response = await apiSyncDevices("Home Assistant");
      ElMessage.success(`同步完成，更新 ${response.synced_count} 台设备`);
      await loadDevices();
    },
    {
      onError: (error) =>
        ElMessage.error(error instanceof Error ? error.message : "设备同步失败"),
    },
  );

  const { loading: batchDeleting, run: confirmBatchDelete } = useAsyncAction(
    async () => {
      const ids = batchDeletingIds.value;
      if (!ids.length) {
        batchDeleteDialogOpen.value = false;
        return;
      }

      let successCount = 0;
      let failCount = 0;

      for (const id of ids) {
        try {
          await apiDeleteDevice(id);
          successCount++;
        } catch {
          failCount++;
        }
      }

      batchDeleteDialogOpen.value = false;
      batchDeletingIds.value = [];

      if (failCount === 0) {
        ElMessage.success(`已成功删除 ${successCount} 台设备`);
      } else {
        ElMessage.warning(`已删除 ${successCount} 台，${failCount} 台删除失败`);
      }

      selectedDeviceIds.value = [];
      batchMode.value = false;
      await loadDevices();
    },
  );

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

  const toggleSelectDevice = (device: Device) => {
    const id = device.id;
    const index = selectedDeviceIds.value.indexOf(id);
    if (index > -1) {
      selectedDeviceIds.value.splice(index, 1);
    } else {
      selectedDeviceIds.value.push(id);
    }
  };

  const clearSelection = () => {
    selectedDeviceIds.value = [];
  };

  const toggleBatchMode = () => {
    batchMode.value = !batchMode.value;
    if (!batchMode.value) {
      clearSelection();
    }
  };

  const batchDeleteDevices = (ids: number[]) => {
    batchDeletingIds.value = ids;
    batchDeleteDialogOpen.value = true;
  };

  const runBatch = () => {
    if (!devices.value.length) {
      ElMessage.warning("当前没有可删除的设备");
      return;
    }
    batchDeletingIds.value = devices.value.map((d) => d.id);
    batchDeleteDialogOpen.value = true;
  };

  const cancelBatchDelete = () => {
    if (batchDeleting.value || deleting.value) return;
    batchDeleteDialogOpen.value = false;
    batchDeletingIds.value = [];
  };

  const batchDeletingDevices = computed(() => {
    const ids = batchDeletingIds.value;
    if (!ids.length) return [];
    return devices.value.filter((d) => ids.includes(d.id));
  });

  const runQuickAction = (key: DeviceQuickActionKey) => {
    if (key === "delete") {
      void runBatch();
      return;
    }

    if (key === "logs") {
      if (selectedId.value === null) {
        ElMessage.warning("请先选择设备");
        return;
      }

      const device = devices.value.find((d) => d.id === selectedId.value);
      logDeviceName.value = device?.name ?? "";

      void apiListDeviceLogs(selectedId.value)
        .then((logs) => {
          deviceLogs.value = logs;
          logDialogOpen.value = true;
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

  const logActionLabel = (action: string): string => {
    return logActionLabels[action] ?? action;
  };

  const closeLogDialog = () => {
    logDialogOpen.value = false;
    deviceLogs.value = [];
    logDeviceName.value = "";
  };

  return {
    addDevice,
    batchDeleteDialogOpen,
    batchMode,
    selectedDeviceIds,
    batchDeleting,
    batchDeletingIds,
    batchDeletingDevices,
    toggleSelectDevice,
    clearSelection,
    toggleBatchMode,
    batchDeleteDevices,
    cancelBatchDelete,
    cancelRemoveDevice,
    confirmBatchDelete,
    confirmRemoveDevice,
    deleteDialogOpen,
    deleting,
    deletingDevice,
    devices,
    deviceLogs,
    editingDevice,
    editorOpen,
    filters,
    loading,
    logActionLabel,
    logDeviceName,
    logDialogOpen,
    closeLogDialog,
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
    loadDevicesDebounced,
    viewMode,
    setViewMode,
    toggleFavorite,
    isFavorite,
    favoriteDeviceIds,
  };
};
