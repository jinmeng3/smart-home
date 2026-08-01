<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
    deleteDevice,
    listDevices,
    syncDevices,
} from "../api/device";
import DeviceDetail from "../components/device/DeviceDetail.vue";
import DeviceList from "../components/device/DeviceList.vue";
import DeviceQuickActions from "../components/device/DeviceQuickActions.vue";
import DeviceStatsCard from "../components/device/DeviceStatsCard.vue";
import DeviceToolbar from "../components/device/DeviceToolbar.vue";
import PlatformStatus from "../components/device/PlatformStatus.vue";
import type { Device, DeviceFilters, DeviceStatus, DeviceType } from "../types/device";

const filters = reactive<DeviceFilters>({
    page: 1,
    pageSize: 10,
    keyword: "",
    type: "",
    status: "",
    room: "",
});
const devices = ref<Device[]>([]);
const total = ref(0);
const loading = ref(false);
const syncing = ref(false);
const selectedId = ref<number | null>(null);
const sort = ref<"updated" | "name" | "status">("updated");

const selectedDevice = computed(
    () => devices.value.find((device) => device.id === selectedId.value) ?? null,
);

const rooms = computed(() =>
    Array.from(new Set(devices.value.map((device) => device.room))).filter(Boolean),
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
    offline: devices.value.filter((device) => device.status === "offline").length,
    warning: devices.value.filter((device) => device.status === "warning").length,
    monthlyNew: devices.value.length,
}));

const platforms = computed(() => {
    const names = ["Home Assistant", "Matter", "Zigbee", "MQTT"];

    return names.map((name) => {
        const connected = devices.value.some((device) => device.connection === name);
        return {
            name,
            connected,
            status: connected ? "已连接" : "未连接",
        };
    });
});

const loadDevices = async () => {
    loading.value = true;

    try {
        const response = await listDevices(filters);
        devices.value = response.items;
        total.value = response.total;

        const firstDevice = response.items[0];

        if (!selectedId.value && firstDevice) {
            selectedId.value = firstDevice.id;
        }
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
};

const addDevice = () => {
    ElMessage.info("添加设备接口已预留");
};

const editDevice = (device: Device) => {
    selectedId.value = device.id;
    ElMessage.info("编辑设备接口已预留");
};

const removeDevice = async (device: Device) => {
    try {
        await ElMessageBox.confirm(`确认删除 ${device.name}？`, "删除设备", {
            confirmButtonText: "删除",
            cancelButtonText: "取消",
            type: "warning",
        });
    } catch {
        return;
    }

    try {
        await deleteDevice(device.id);
        ElMessage.success("设备已删除");
        await loadDevices();
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "设备删除失败");
    }
};

const runSync = async () => {
    syncing.value = true;

    try {
        const response = await syncDevices("Home Assistant");
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

const runQuickAction = (key: "scan" | "group" | "firmware" | "logs") => {
    const messageMap: Record<typeof key, string> = {
        scan: "扫描新设备接口已预留",
        group: "批量分组接口已预留",
        firmware: "固件更新接口已预留",
        logs: "设备日志接口已预留",
    };

    ElMessage.info(messageMap[key]);
};

watch(
    () => [
        filters.page,
        filters.pageSize,
        filters.keyword,
        filters.type,
        filters.status,
        filters.room,
    ],
    () => {
        void loadDevices();
    },
);

onMounted(() => {
    void loadDevices();
});
</script>

<template>
    <div class="contents">
        <section class="device-management-page">
            <header class="device-page-header">
                <div>
                    <h1>设备管理</h1>
                    <p>统一管理家庭设备、状态、分组与接入平台</p>
                </div>
            </header>

            <DeviceToolbar
                :keyword="filters.keyword"
                :room="filters.room"
                :rooms="rooms"
                :status="filters.status"
                :syncing="syncing"
                :type="filters.type"
                @add="addDevice"
                @batch="runBatch"
                @sync="runSync"
                @update:keyword="updateKeyword"
                @update:room="updateRoom"
                @update:status="updateStatus"
                @update:type="updateType"
            />

            <div class="device-stats-grid">
                <DeviceStatsCard
                    icon="online-device"
                    label="在线设备"
                    :value="stats.online"
                    tone="success"
                    :delay="0"
                />
                <DeviceStatsCard
                    icon="offline-device"
                    label="离线设备"
                    :value="stats.offline"
                    tone="muted"
                    :delay="50"
                />
                <DeviceStatsCard
                    icon="warning"
                    label="告警设备"
                    :value="stats.warning"
                    tone="warning"
                    :delay="100"
                />
                <DeviceStatsCard
                    icon="new-device"
                    label="本月新增"
                    :value="stats.monthlyNew"
                    tone="primary"
                    :delay="150"
                />
            </div>

            <DeviceList
                :active-type="filters.type"
                :devices="sortedDevices"
                :loading="loading"
                :page="filters.page"
                :page-size="filters.pageSize"
                :selected-id="selectedId"
                :sort="sort"
                :total="total"
                @edit="editDevice"
                @remove="removeDevice"
                @select="selectDevice"
                @update:active-type="updateType"
                @update:page="updatePage"
                @update:page-size="updatePageSize"
                @update:sort="sort = $event"
            />
        </section>

        <aside class="device-right-panel">
            <DeviceDetail :device="selectedDevice" />
            <DeviceQuickActions @action="runQuickAction" />
            <PlatformStatus :platforms="platforms" />
        </aside>
    </div>
</template>

<style scoped>
.device-management-page {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 16px;
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 16px;
    background: var(--color-workspace-background);
    padding: 20px;
    box-shadow: var(--shadow-card);
    animation: device-page-enter 240ms var(--motion-ease) both;
}

.device-page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
}

.device-page-header h1 {
    margin: 0;
    font-size: 26px;
    font-weight: 900;
}

.device-page-header p {
    margin: 8px 0 0;
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 700;
}

.device-stats-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
}

.device-right-panel {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    border-left: 1px solid var(--color-border-default);
    background: var(--color-sidebar-background);
    padding: 0 2px 0 10px;
}

@keyframes device-page-enter {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: reduce) {
    .device-management-page {
        animation-duration: 1ms;
    }
}
</style>
