<script setup lang="ts">
import { computed, ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import type { Room } from "../../../types/room";

interface DeviceInfo {
    name: string;
    type: string;
    status: "online" | "offline" | "warning";
    detail: string;
    updatedAt: string;
    icon: string;
    id: string;
}

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

// Mock data — replace with API call in production
const devices = ref<DeviceInfo[]>([
    { name: "吸顶灯", type: "灯光", status: "online", detail: "亮度 80%", updatedAt: "今天 10:25", icon: "light", id: "1" },
    { name: "落地灯", type: "灯光", status: "online", detail: "亮度 60%", updatedAt: "今天 10:25", icon: "light", id: "2" },
    { name: "电视", type: "影音", status: "online", detail: "HDMI 1", updatedAt: "今天 10:24", icon: "device-management", id: "3" },
    { name: "空调", type: "环境", status: "online", detail: "24°C | 制冷", updatedAt: "今天 10:24", icon: "air-conditioner", id: "4" },
    { name: "窗帘电机", type: "窗帘", status: "online", detail: "打开 70%", updatedAt: "今天 10:24", icon: "curtain", id: "5" },
    { name: "空气净化器", type: "环境", status: "online", detail: "自动模式 | 优", updatedAt: "今天 10:24", icon: "sensor", id: "6" },
    { name: "智能插座", type: "电源", status: "online", detail: "功率 35W", updatedAt: "今天 10:24", icon: "plug", id: "7" },
    { name: "温湿度传感器", type: "传感器", status: "online", detail: "温度 24°C | 湿度 55%", updatedAt: "今天 10:24", icon: "humidity", id: "8" },
    { name: "烟雾报警器", type: "安防", status: "offline", detail: "离线", updatedAt: "昨天 22:15", icon: "sensor", id: "9" },
    { name: "智能门锁", type: "安防", status: "warning", detail: "电量不足", updatedAt: "今天 09:30", icon: "lock", id: "10" },
]);

const loading = ref(false);
const deviceTypeOptions = ["灯光", "影音", "环境", "窗帘", "电源", "传感器", "安防"];
const deviceStatusOptions = [
    { value: "online", label: "在线" },
    { value: "offline", label: "离线" },
    { value: "warning", label: "告警" },
];

const deviceCount = computed(() => props.room?.deviceCount ?? devices.value.length);
const onlineCount = computed(() => props.room?.onlineCount ?? devices.value.filter((d) => d.status === "online").length);
const groupCount = 6;

const filteredDevices = computed(() => {
    const keyword = deviceKeyword.value.trim().toLowerCase();
    const type = deviceTypeFilter.value;
    const status = deviceStatusFilter.value;

    return devices.value.filter((device) => {
        if (keyword && !device.name.toLowerCase().includes(keyword)) {
            return false;
        }
        if (type && device.type !== type) {
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
                    <span class="stat-icon"><SvgIcon name="check" size="sm" /></span>
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
                    <option value="">全部类型</option>
                    <option v-for="type in deviceTypeOptions" :key="type" :value="type">{{ type }}</option>
                </select>
                <select v-model="deviceStatusFilter" class="filter-select">
                    <option value="">全部状态</option>
                    <option v-for="opt in deviceStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
                <button type="button" class="toolbar-btn toolbar-btn-primary" title="批量开关">
                    <SvgIcon name="power" size="sm" />批量开关
                </button>
                <button type="button" class="toolbar-btn" title="分组管理">
                    <SvgIcon name="group" size="sm" />分组管理
                </button>
                <button type="button" class="toolbar-btn" title="设为常用">
                    <SvgIcon name="check" size="sm" />设为常用
                </button>
            </div>

            <!-- Device table -->
            <div class="device-table">
                <div class="table-header">
                    <span>设备名称</span>
                    <span>所属分组</span>
                    <span>当前状态</span>
                    <span>电量 / 模式</span>
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
                        <span class="device-icon"><SvgIcon :name="device.icon" size="sm" /></span>
                        {{ device.name }}
                    </span>
                    <span class="cell-type">{{ device.type }}</span>
                    <span :class="['status-badge', statusClass[device.status]]">
                        {{ statusLabel[device.status] }}
                    </span>
                    <span class="cell-detail">{{ device.detail }}</span>
                    <span class="cell-time">{{ device.updatedAt }}</span>
                    <span class="cell-actions">
                        <button
                            type="button"
                            class="action-btn"
                            :title="device.status === 'online' ? '关闭设备' : '开启设备'"
                        >
                            <SvgIcon name="power" size="sm" />
                        </button>
                        <button type="button" class="action-btn" title="更多操作">
                            <SvgIcon name="more" size="sm" />
                        </button>
                    </span>
                </div>
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
    gap: 4px;
    min-width: 120px;
    height: 36px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 8px;
    transition: border-color 0.15s;
}

.search-box:focus-within {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.search-icon {
    flex-shrink: 0;
    color: var(--color-text-tertiary);
    pointer-events: none;
}

.search-box input {
    flex: 1;
    min-width: 0;
    height: 100%;
    border: none;
    background: none;
    padding: 0;
    font-size: 13px;
    outline: none;
    color: var(--color-text-primary);
}

.search-box input::placeholder {
    color: var(--color-text-tertiary);
}

.search-clear {
    display: grid;
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    place-items: center;
    border: none;
    border-radius: 50%;
    background: var(--color-border);
    color: var(--color-card-bg);
    cursor: pointer;
    padding: 0;
    transition: background 0.12s;
}

.search-clear:hover {
    background: var(--color-text-tertiary);
}

.filter-select {
    width: 110px;
    height: 36px;
    min-height: 0;
    flex-shrink: 0;
    border: 1px solid var(--color-border);
    border-radius: 8px;
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
    height: 36px;
    flex-shrink: 0;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 12px;
    font-size: 12px;
    color: var(--color-text-primary);
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
}

.toolbar-btn:hover {
    background: var(--color-surface-subtle);
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
    color: #fff;
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
    background: var(--color-primary-50);
    color: var(--color-primary-600);
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