import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { useAsyncAction } from "./useAsyncAction";
import { useDeviceQuery } from "./useDeviceQuery";
import { usePlatformAccess } from "./usePlatformAccess";
import {
  createDevice as apiCreateDevice,
  deleteDevice as apiDeleteDevice,
  getDevice as apiGetDevice,
  listDeviceLogs as apiListDeviceLogs,
  updateDevice as apiUpdateDevice,
} from "../api/device";
import type {
  Device,
  DeviceCreatePayload,
  DeviceDetail,
  DeviceFilters,
  DeviceLog,
  DeviceQuickActionKey,
} from "../types/device";

export type { DeviceQuickActionKey } from "../types/device";

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

/**
 * 设备管理页面控制器——组合查询/平台/选中/编辑/删除/日志等模块。
 * 数据查询（筛选/分页/请求取消）见 useDeviceQuery，平台派生见 usePlatformAccess。
 * 异步操作统一走 useAsyncAction（pending/execute），防重复提交并自动清理状态。
 */
export const useDeviceManagementController = () => {
  /* ── 选中设备 ─────────────────────────────────────────────────── */
  const selectedId = ref<number | null>(null);
  const selectedDevice = ref<DeviceDetail | null>(null);

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

  const selectDevice = (device: Device) => {
    selectedId.value = device.id;
    void loadSelectedDevice();
  };

  /* ── 数据查询（useDeviceQuery：筛选/分页/防抖/请求取消） ──────── */
  const query = useDeviceQuery({
    onLoaded: async (items) => {
      const selectedExists = items.some(
        (device) => device.id === selectedId.value,
      );
      selectedId.value = selectedExists
        ? selectedId.value
        : (items[0]?.id ?? null);
      await loadSelectedDevice();
    },
    onError: (error) => {
      ElMessage.error(
        error instanceof Error ? error.message : "设备列表加载失败",
      );
    },
  });

  const { devices, filters, loading, total } = query;
  const loadDevices = query.loadDevices;

  /* ── 接入平台（usePlatformAccess：平台派生 + 同步入口） ────────── */
  const platformAccess = usePlatformAccess(devices);
  const { connectedCount, connectedPlatforms, platforms } = platformAccess;

  /* ── 排序 / 收藏过滤（列表展示层） ─────────────────────────────── */
  const sort = ref<"updated" | "name" | "status">("updated");

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

  const isFavorite = (deviceId: number) =>
    favoriteDeviceIds.value.includes(deviceId);

  // Load favorites on initialization
  loadFavorites();

  const filteredDevices = computed(() => {
    let result = devices.value;
    if (viewMode.value === "favorite") {
      result = result.filter((d) => isFavorite(d.id));
    }
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

  /* ── 新增 / 编辑 ───────────────────────────────────────────────── */
  const editorOpen = ref(false);
  const editingDevice = ref<Device | null>(null);

  const { pending: saving, execute: saveDevice } = useAsyncAction(
    async (payload: DeviceCreatePayload) => {
      if (editingDevice.value) {
        await apiUpdateDevice(editingDevice.value.id, payload);
        // 局部更新——先更新本地设备，再后台刷新保持一致性
        const idx = devices.value.findIndex(
          (d) => d.id === editingDevice.value!.id,
        );
        if (idx >= 0) {
          const current = devices.value[idx];
          if (!current) return;
          const { name, room, type, brand, connection, firmware, icon, color } =
            payload;
          devices.value[idx] = {
            ...current,
            name,
            room,
            type,
            brand,
            connection,
            firmware: firmware ?? current.firmware,
            icon: icon ?? current.icon,
            color: color ?? current.color,
          };
        }
        ElMessage.success("设备已更新");
      } else {
        const created = await apiCreateDevice(payload);
        selectedId.value = created.id;
        ElMessage.success("设备已添加");
      }

      editorOpen.value = false;
      await query.loadDevices();
    },
    {
      onError: (error) =>
        ElMessage.error(error instanceof Error ? error.message : "设备保存失败"),
    },
  );

  const addDevice = () => {
    editingDevice.value = null;
    editorOpen.value = true;
  };

  const editDevice = (device: Device) => {
    selectedId.value = device.id;
    editingDevice.value = device;
    editorOpen.value = true;
  };

  /* ── 单个删除 ─────────────────────────────────────────────────── */
  const deleteDialogOpen = ref(false);
  const deletingDevice = ref<Device | null>(null);

  const removeDevice = (device: Device) => {
    deletingDevice.value = device;
    deleteDialogOpen.value = true;
  };

  const cancelRemoveDevice = () => {
    if (deleting.value) return;
    deleteDialogOpen.value = false;
    deletingDevice.value = null;
  };

  const { pending: deleting, execute: confirmRemoveDevice } = useAsyncAction(
    async () => {
      if (!deletingDevice.value) return;
      const device = deletingDevice.value;
      await apiDeleteDevice(device.id);
      // 局部更新——先移除本地设备
      const idx = devices.value.findIndex((d) => d.id === device.id);
      if (idx >= 0) {
        devices.value.splice(idx, 1);
        total.value = Math.max(0, total.value - 1);
      }
      ElMessage.success("设备已删除");
      deleteDialogOpen.value = false;
      deletingDevice.value = null;
      await query.loadDevices();
    },
    {
      onError: (error) =>
        ElMessage.error(error instanceof Error ? error.message : "设备删除失败"),
    },
  );

  /* ── 批量删除 ─────────────────────────────────────────────────── */
  const batchDeleteDialogOpen = ref(false);
  const batchMode = ref(false);
  const selectedDeviceIds = ref<number[]>([]);
  const batchDeletingIds = ref<number[]>([]);
  const batchDeletingDevices = computed(() => {
    const ids = batchDeletingIds.value;
    if (!ids.length) return [];
    return devices.value.filter((d) => ids.includes(d.id));
  });

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

  const { pending: batchDeleting, execute: confirmBatchDelete } = useAsyncAction(
    async () => {
      const ids = batchDeletingIds.value;
      if (!ids.length) {
        batchDeleteDialogOpen.value = false;
        return;
      }

      let successCount = 0;
      let failCount = 0;
      const removedIds = new Set<number>();

      for (const id of ids) {
        try {
          await apiDeleteDevice(id);
          removedIds.add(id);
          successCount++;
        } catch {
          failCount++;
        }
      }

      // 局部更新——批量移除本地设备
      devices.value = devices.value.filter((d) => !removedIds.has(d.id));
      total.value = Math.max(0, total.value - successCount);

      batchDeleteDialogOpen.value = false;
      batchDeletingIds.value = [];

      if (failCount === 0) {
        ElMessage.success(`已成功删除 ${successCount} 台设备`);
      } else {
        ElMessage.warning(`已删除 ${successCount} 台，${failCount} 台删除失败`);
      }

      selectedDeviceIds.value = [];
      batchMode.value = false;
      await query.loadDevices();
    },
  );

  /* ── 平台同步 / 快捷操作 / 日志 ───────────────────────────────── */
  const { pending: syncing, execute: runSync } = useAsyncAction(
    async () => {
      const response = await platformAccess.syncAllPlatforms();
      ElMessage.success(`同步完成，更新 ${response.synced_count} 台设备`);
      query.loadDevices();
      return response.synced_count;
    },
    {
      onError: (error) =>
        ElMessage.error(error instanceof Error ? error.message : "设备同步失败"),
    },
  );

  const logDialogOpen = ref(false);
  const deviceLogs = ref<DeviceLog[]>([]);
  const logDeviceName = ref("");

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
    connectedCount,
    connectedPlatforms,
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
    loadDevices,
    logActionLabel,
    logDeviceName,
    logDialogOpen,
    closeLogDialog,
    platforms,
    removeDevice,
    rooms: query.rooms,
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
    updateFilter: query.updateFilter,
    updatePage: query.updatePage,
    updatePageSize: query.updatePageSize,
    editDevice,
    viewMode,
    setViewMode,
    toggleFavorite,
    isFavorite,
    favoriteDeviceIds,
  };
};