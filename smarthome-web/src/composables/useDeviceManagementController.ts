import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { deviceService } from "../services/device";
import type {
  Device,
  DeviceCreatePayload,
  DeviceDetail,
  DeviceFilters,
  DevicePlatform,
  DeviceStatus,
  DeviceType,
} from "../types/device";

export type DeviceSortKey = "updated" | "name" | "status";
export type DeviceQuickActionKey = "scan" | "group" | "firmware" | "logs";

const platformNames: DevicePlatform[] = [
  "Home Assistant",
  "Matter",
  "Zigbee",
  "MQTT",
];

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

  const rooms = computed(() =>
    Array.from(new Set(devices.value.map((device) => device.room))).filter(
      Boolean,
    ),
  );

  const sortedDevices = computed(() => {
    const nextDevices = [...devices.value];

    if (sort.value === "name") {
      return nextDevices.sort((first, second) =>
        first.name.localeCompare(second.name, "zh-CN"),
      );
    }

    if (sort.value === "status") {
      return nextDevices.sort((first, second) =>
        first.status.localeCompare(second.status),
      );
    }

    return nextDevices;
  });

  const stats = computed(() => ({
    online: devices.value.filter((device) => device.status === "online").length,
    offline: devices.value.filter((device) => device.status === "offline")
      .length,
    warning: devices.value.filter((device) => device.status === "warning")
      .length,
    monthlyNew: devices.value.length,
  }));

  const platforms = computed(() =>
    platformNames.map((name) => {
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
      selectedDevice.value = await deviceService.get(selectedId.value);
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
      const response = await deviceService.list(filters);
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

  const updateKeyword = (value: string) => {
    filters.keyword = value;
    filters.page = 1;
  };

  const updateRoom = (value: string) => {
    filters.room = value;
    filters.page = 1;
  };

  const updateType = (value: DeviceType | "") => {
    filters.type = value;
    filters.page = 1;
  };

  const updateStatus = (value: DeviceStatus | "") => {
    filters.status = value;
    filters.page = 1;
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
        await deviceService.update(editingDevice.value.id, payload);
        ElMessage.success("设备已更新");
      } else {
        const created = await deviceService.create(payload);
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
      await deviceService.remove(device.id);
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
      const response = await deviceService.sync("Home Assistant");
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

      void deviceService.listLogs(selectedId.value)
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

    const messageMap: Record<Exclude<DeviceQuickActionKey, "logs">, string> = {
      scan: "扫描新设备接口已预留",
      group: "批量分组接口已预留",
      firmware: "固件更新接口已预留",
    };

    ElMessage.info(messageMap[key]);
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
    updateKeyword,
    updatePage,
    updatePageSize,
    updateRoom,
    updateStatus,
    updateType,
    editDevice,
    loadDevices,
  };
};
