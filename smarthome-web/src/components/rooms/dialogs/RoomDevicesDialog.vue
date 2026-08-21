<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { getRoomDevices, updateRoomDevice } from "../../../api/room";
import type { Room, RoomDeviceListItem } from "../../../types/room";
import { useLatestRequest } from "../../../composables/useLatestRequest";

const router = useRouter();

const props = defineProps<{
    modelValue: boolean;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const deviceKeyword = ref("");
const deviceTypeFilter = ref("");
const deviceStatusFilter = ref("");

const title = "房间设备管理";
const description = computed(
    () => `统一管理${props.room?.name ?? "房间"}内的设备状态、分组与快捷控制`,
);

const devices = ref<RoomDeviceListItem[]>([]);
const togglingIds = ref<Set<number>>(new Set());
const { invalidate, loading, run } = useLatestRequest();
const deviceStatusOptions = [
    { value: "", label: "全部状态" },
    { value: "online", label: "在线" },
    { value: "offline", label: "离线" },
    { value: "warning", label: "告警" },
];

const loadDevices = async () => {
    if (!props.room) return;
    const roomId = props.room.id;
    await run(
        () =>
            getRoomDevices(roomId, {
                keyword: deviceKeyword.value || undefined,
                status: deviceStatusFilter.value || undefined,
            }),
        (response) => {
            devices.value = response.items;
        },
        () => {
            devices.value = [];
        },
    );
};

watch(
    () => props.modelValue,
    (open) => {
        if (open && props.room) {
            loadDevices();
        }
    },
    { immediate: true },
);

let searchTimer: ReturnType<typeof setTimeout> | undefined;
watch(
    () => [deviceKeyword.value, deviceTypeFilter.value, deviceStatusFilter.value],
    () => {
        if (!props.modelValue) return;
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            loadDevices();
        }, 300);
    },
);

onBeforeUnmount(() => {
    clearTimeout(searchTimer);
    invalidate();
});

const deviceCount = computed(() => devices.value.length);
const onlineCount = computed(() => devices.value.filter((d) => d.status === "online" || d.status === "running").length);
const groupCount = computed(() => {
    const groups = new Set(devices.value.map((d) => d.group));
    return groups.size;
});

const deviceTypeOptions = computed(() => {
    const groups = new Set(devices.value.map((d) => d.group));
    return ["", ...groups].filter(Boolean);
});

const filteredDevices = computed(() => {
    const keyword = deviceKeyword.value.trim().toLowerCase();
    const type = deviceTypeFilter.value;
    const status = deviceStatusFilter.value;

    return devices.value.filter((device) => {
        if (keyword && !device.name.toLowerCase().includes(keyword)) {
            return false;
        }
        if (type && device.group !== type) {
            return false;
        }
        if (status && device.status !== status) {
            return false;
        }
        return true;
    });
});

const statusLabel: Record<string, string> = {
    online: "在线",
    offline: "离线",
    warning: "告警",
};

const statusClass: Record<string, string> = {
    online: "status-online",
    offline: "status-offline",
    warning: "status-warning",
};

const formatTime = (value: string): string => {
    if (!value) return "暂无";
    const time = new Date(value);
    if (Number.isNaN(time.getTime())) return value;
    const now = new Date();
    const diffMin = Math.floor((now.getTime() - time.getTime()) / 60000);
    if (diffMin < 1) return "刚刚";
    if (diffMin < 60) return `${diffMin} 分钟前`;
    const pad = (n: number) => String(n).padStart(2, "0");
    const clock = `${pad(time.getHours())}:${pad(time.getMinutes())}`;
    if (time.toDateString() === now.toDateString()) return `今天 ${clock}`;
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    if (time.toDateString() === yesterday.toDateString()) return `昨天 ${clock}`;
    return `${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${clock}`;
};

const toggleDevice = async (device: RoomDeviceListItem) => {
    if (!props.room) return;
    togglingIds.value = new Set([...togglingIds.value, device.id]);
    const newStatus = device.status === "online" || device.status === "running" ? "offline" : "online";
    try {
        await updateRoomDevice(props.room.id, device.id, newStatus);
        devices.value = devices.value.map((d) =>
            d.id === device.id ? { ...d, status: newStatus } : d,
        );
        ElMessage.success(`${device.name} 已${newStatus === "online" ? "开启" : "关闭"}`);
    } catch (e) {
        ElMessage.error(e instanceof Error ? e.message : "操作失败");
    } finally {
        const next = new Set(togglingIds.value);
        next.delete(device.id);
        togglingIds.value = next;
    }
};

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="title"
        :description="description"
        confirm-text="保存设置"
        width="large"
        @cancel="close"
        @confirm="close"
        @update:model-value="close"
    >
        <div class="devices-dialog">
            <!-- Header stats -->
            <header class="devices-header">
                <div class="room-summary">
                    <span class="room-icon"><SvgIcon name="room" size="lg" /></span>
                    <div class="room-info">
                        <h3>{{ room?.name }}</h3>
                        <small class="status-dot status-online">● 在线</small>
                    </div>
                </div>
                <div class="stat-card stat-card-devices">
                    <span class="stat-icon"><SvgIcon name="device-management" size="sm" /></span>
                    <div class="stat-body">
                        <span class="stat-label">设备总数</span>
                        <strong class="stat-value">{{ deviceCount }} <span class="stat-unit">个设备</span></strong>
                    </div>
                </div>
                <div class="stat-card stat-card-online">
                    <span class="stat-icon"><SvgIcon name="online-device" size="sm" /></span>
                    <div class="stat-body">
                        <span class="stat-label">在线设备</span>
                        <strong class="stat-value">{{ onlineCount }} <span class="stat-unit">/ {{ deviceCount }}</span></strong>
                    </div>
                </div>
                <div class="stat-card stat-card-groups">
                    <span class="stat-icon"><SvgIcon name="group" size="sm" /></span>
                    <div class="stat-body">
                        <span class="stat-label">常用分组</span>
                        <strong class="stat-value">{{ groupCount }} <span class="stat-unit">个分组</span></strong>
                    </div>
                </div>
            </header>

            <!-- Toolbar -->
            <div class="device-toolbar">
                <div class="search-box" :class="{ 'has-text': deviceKeyword }">
                    <SvgIcon class="search-icon" name="search" size="sm" />
                    <input
                        v-model="deviceKeyword"
                        placeholder="搜索设备名称"
                        type="text"
                    />
                    <button
                        v-if="deviceKeyword"
                        class="search-clear"
                        type="button"
                        title="清除搜索"
                        @click="deviceKeyword = ''"
                    >
                        <SvgIcon name="close" size="sm" />
                    </button>
                </div>
                <select v-model="deviceTypeFilter" class="filter-select">
                    <option value="">全部分组</option>
                    <option v-for="type in deviceTypeOptions" :key="type" :value="type">{{ type }}</option>
                </select>
                <select v-model="deviceStatusFilter" class="filter-select">
                    <option v-for="opt in deviceStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
            </div>

            <!-- Device table -->
            <div class="device-table">
                <div class="table-header">
                    <span>设备名称</span>
                    <span>所属分组</span>
                    <span>当前状态</span>
                    <span>品牌</span>
                    <span>更新时间</span>
                    <span>快捷操作</span>
                </div>

                <div v-if="loading" class="table-loading">
                    <div v-for="n in 5" :key="n" class="skeleton-row">
                        <div class="skeleton-cell" style="width: 120px" />
                        <div class="skeleton-cell" style="width: 60px" />
                        <div class="skeleton-cell" style="width: 60px" />
                        <div class="skeleton-cell" style="width: 100px" />
                        <div class="skeleton-cell" style="width: 80px" />
                        <div class="skeleton-cell" style="width: 40px" />
                    </div>
                </div>

                <div v-else-if="filteredDevices.length === 0" class="table-empty">
                    <SvgIcon name="device-management" size="lg" />
                    <p>没有匹配的设备</p>
                    <small>试试调整搜索条件或筛选类型</small>
                </div>

                <div
                    v-for="(device, index) in filteredDevices"
                    :key="device.id"
                    class="table-row"
                    :class="{ 'row-alt': index % 2 === 1 }"
                    :style="{ '--row-index': index }"
                    tabindex="0"
                >
                    <span class="cell-name">
                      <span class="device-icon" :style="{ '--device-color': device.color || '#6b7280' }"><SvgIcon :name="device.icon || 'device-management'" size="sm" /></span>
                        {{ device.name }}
                    </span>
                    <span class="cell-type">{{ device.group }}</span>
                    <span :class="['status-badge', statusClass[device.status]]">
                        {{ statusLabel[device.status] ?? device.status }}
                    </span>
                    <span class="cell-detail">{{ device.brand || "—" }}</span>
                    <span class="cell-time">{{ formatTime(device.updatedAt) }}</span>
                    <span class="cell-actions">
                        <button
                            type="button"
                            class="action-btn"
                            :class="{ 'is-on': device.status === 'online' || device.status === 'running' }"
                            :disabled="togglingIds.has(device.id)"
                            :title="(device.status === 'online' || device.status === 'running') ? '关闭设备' : '开启设备'"
                            @click="toggleDevice(device)"
                        >
                            <SvgIcon name="power" size="sm" />
                        </button>
                        <button type="button" class="action-btn" title="前往设备管理" @click="close(); router.push('/devices')">
                            <SvgIcon name="more" size="sm" />
                        </button>
                    </span>
                </div>
            </div>

            <div class="table-footer">
                共 <strong>{{ filteredDevices.length }}</strong> 个设备
                <span v-if="filteredDevices.length !== devices.length">（筛选自 {{ devices.length }} 个）</span>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
/* ===== Header ===== */
.devices-header {
    display: grid;
    grid-template-columns: 1.2fr repeat(3, 1fr);
    gap: 10px;
}

.room-summary,
.stat-card {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 11px;
}

.stat-card {
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
    gap: 10px;
    padding: 12px 14px;
}

.stat-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 8px;
}

.stat-card-devices .stat-icon {
    background: linear-gradient(135deg, #e0f2fe, #bae6fd);
    color: #0284c7;
}

.stat-card-online .stat-icon {
    background: linear-gradient(135deg, #dcfce7, #bbf7d0);
    color: #16a34a;
}

.stat-card-groups .stat-icon {
    background: linear-gradient(135deg, #f3e8ff, #e9d5ff);
    color: #9333ea;
}

.stat-body {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
}

.stat-label {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.stat-value {
    font-size: 22px;
    line-height: 1.2;
}

.stat-unit {
    color: var(--color-text-tertiary);
    font-size: 10px;
    font-weight: 400;
    font-style: normal;
}

.room-icon {
    display: grid;
    width: 50px;
    height: 50px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 9px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.room-info h3 {
    margin: 0;
    font-size: 16px;
}

.room-info small {
    color: var(--color-success) !important;
}

/* ===== Toolbar ===== */
.device-toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin: 12px 0;
}

.search-box {
    display: flex;
    flex: 1 1 200px;
    align-items: center;
    gap: 6px;
    min-width: 120px;
    height: 40px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0 10px;
    transition: border-color 180ms var(--motion-ease), box-shadow 180ms var(--motion-ease);
}

.search-box:focus-within {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.search-icon {
    flex-shrink: 0;
    color: var(--color-text-muted);
    pointer-events: none;
}

.search-box input {
    flex: 1;
    min-width: 0;
    height: 100%;
    min-height: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    padding: 0;
    font-size: 14px;
    font-weight: 600;
    box-shadow: none !important;
    outline: none;
    color: var(--color-text-primary);
}

.search-box input:focus,
.search-box input:focus-visible {
    border: 0 !important;
    box-shadow: none !important;
}

.search-box input::placeholder {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
}

.search-clear {
    display: grid;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    place-items: center;
    border: none;
    border-radius: 50%;
    background: var(--color-surface-subtle);
    color: var(--color-text-muted);
    cursor: pointer;
    padding: 0;
    transition: background 180ms var(--motion-ease);
}

.search-clear:hover {
    background: var(--color-border);
    color: var(--color-text-secondary);
}

.filter-select {
    width: 110px;
    height: 40px;
    min-height: 0;
    flex-shrink: 0;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0 10px;
    font-size: 13px;
    outline: none;
    color: var(--color-text-primary);
    cursor: pointer;
}

.filter-select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.toolbar-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    height: 40px;
    flex-shrink: 0;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0 14px;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-primary);
    cursor: pointer;
    transition: background 180ms var(--motion-ease), border-color 180ms var(--motion-ease);
}

.toolbar-btn:hover {
    background: var(--color-surface-hover);
    border-color: var(--color-primary-300);
}

.toolbar-btn-primary {
    background: var(--color-primary-600);
    border-color: var(--color-primary-600);
    color: #fff;
}

.toolbar-btn-primary:hover {
    background: var(--color-primary-500);
    border-color: var(--color-primary-500);
}

/* ===== Device table ===== */
.device-table {
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}

.table-header,
.table-row {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr 1.2fr 1.1fr 0.7fr;
    align-items: center;
    gap: 8px;
    padding: 12px 14px;
    font-size: 13px;
}

.table-header {
    background: var(--color-surface-subtle);
    font-weight: 700;
    color: var(--color-text-secondary);
}

.table-row {
    border-top: 1px solid var(--color-border-subtle);
    cursor: default;
    transition: background 0.15s;
    outline: none;
    animation: row-fade-in 0.3s ease both;
    animation-delay: calc(var(--row-index, 0) * 30ms);
}

.row-alt {
    background: var(--color-surface-subtle);
}

.table-row:hover {
    background: var(--color-primary-50);
}

.table-row:focus-visible {
    box-shadow: inset 0 0 0 2px var(--color-focus-ring);
}

.table-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 10px 14px;
    border-top: 1px solid var(--color-border-subtle);
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}
.table-footer strong {
    color: var(--color-text-secondary);
}
.table-footer span {
    color: var(--color-text-muted);
}

@keyframes row-fade-in {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.cell-name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
}

.device-icon {
    display: grid;
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 7px;
    background: color-mix(in srgb, var(--device-color, #6b7280) 14%, transparent);
    color: var(--device-color, #6b7280);
}

.cell-type {
    color: var(--color-text-tertiary);
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    height: 22px;
    padding: 0 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    width: fit-content;
}

.status-badge.status-online {
    background: #dcfce7;
    color: #16a34a;
}

.status-badge.status-offline {
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.status-badge.status-warning {
    background: #fef3c7;
    color: #d97706;
}

.cell-detail {
    color: var(--color-text-secondary);
}

.cell-time {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

.cell-actions {
    display: flex;
    gap: 4px;
}

.action-btn {
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    background: transparent;
    color: var(--color-text-tertiary);
    cursor: pointer;
    transition: background 0.12s, color 0.12s, border-color 0.12s;
}

.action-btn:hover {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    border-color: var(--color-primary-300);
}

.action-btn.is-on {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    border-color: var(--color-primary-200);
}

.action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.action-btn:disabled:hover {
    background: transparent;
    color: var(--color-text-tertiary);
    border-color: var(--color-border);
}

/* ===== Loading skeleton ===== */
.table-loading {
    padding: 8px 12px;
}

.skeleton-row {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr 1.2fr 1.1fr 0.7fr;
    gap: 8px;
    padding: 10px 0;
}

.skeleton-row + .skeleton-row {
    border-top: 1px solid var(--color-border-subtle);
}

.skeleton-cell {
    height: 14px;
    border-radius: 4px;
    background: var(--color-border-subtle);
    animation: skeleton-pulse 1.4s ease-in-out infinite;
}

@keyframes skeleton-pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.8; }
}

/* ===== Empty state ===== */
.table-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 40px 20px;
    color: var(--color-text-tertiary);
}

.table-empty p {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
}

.table-empty small {
    font-size: 12px;
}

/* ===== Responsive ===== */
@media (max-width: 760px) {
    .devices-header {
        grid-template-columns: 1fr 1fr;
    }

    .devices-header .room-summary {
        grid-column: 1 / -1;
    }

    .device-toolbar {
        gap: 6px;
    }

    .search-box {
        flex: 1 1 100%;
        order: -1;
    }

    .search-box.has-text {
        flex: 1 1 100%;
    }

    .filter-select {
        flex: 1;
        width: auto;
    }

    .toolbar-btn {
        flex: 1;
        justify-content: center;
        min-width: 0;
        padding: 0 8px;
        font-size: 10px;
    }

    .device-table {
        overflow-x: auto;
    }

    .table-header,
    .table-row {
        min-width: 700px;
    }
}
</style>
