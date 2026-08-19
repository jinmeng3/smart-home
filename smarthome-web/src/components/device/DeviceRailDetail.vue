<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import DeviceRailActions, { type RailAction } from "./DeviceRailActions.vue";
import {
    deviceStatusLabelMap,
    deviceTypeIconMap,
    getDeviceTypeIcon,
} from "./deviceMeta";
import type { Device, DeviceDetail } from "../../types/device";

const props = defineProps<{
    device: Device | null;
    syncing?: boolean;
}>();

const emit = defineEmits<{
    action: [key: string];
    sync: [];
}>();

const detailActions: RailAction[] = [
    { key: "edit", label: "编辑", tone: "primary", icon: "edit" },
    { key: "sync", label: "同步", tone: "success", icon: "refresh" },
    { key: "logs", label: "查看日志", tone: "warning", icon: "log" },
];

const deviceIcon = computed(() =>
    props.device
        ? getDeviceTypeIcon(props.device.icon || props.device.type)
        : "device-management",
);

const formatLastOnline = (value: string): string => {
    if (!value) return "暂无";
    const time = new Date(value);
    if (Number.isNaN(time.getTime())) return value;
    const now = new Date();
    const diffMin = Math.floor((now.getTime() - time.getTime()) / 60000);
    const pad = (n: number) => String(n).padStart(2, "0");
    if (diffMin < 1) return "刚刚";
    if (diffMin < 60) return `${diffMin} 分钟前`;
    const clock = `${pad(time.getHours())}:${pad(time.getMinutes())}`;
    if (time.toDateString() === now.toDateString()) return clock;
    return `${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${clock}`;
};

/** 接入平台 → 色调（与列表/状态条一致） */
const platformToneMap: Record<string, string> = {
    "Home Assistant": "orange",
    Matter: "indigo",
    Zigbee: "green",
    MQTT: "purple",
};

const platformTone = (name: string): string => platformToneMap[name] ?? "orange";

/** 最后在线按新旧着色：1 小时内绿色，7 天内青色，更早中性灰 */
const lastOnlineTone = computed(() => {
    const value = props.device?.lastOnline;
    if (!value) return "is-muted";
    const time = new Date(value);
    if (Number.isNaN(time.getTime())) return "is-muted";
    const diffMin = Math.floor((Date.now() - time.getTime()) / 60000);
    if (diffMin < 60) return "is-green";
    if (diffMin < 60 * 24 * 7) return "is-teal";
    return "is-muted";
});

const handleAction = (key: string) => {
    if (key === "sync") {
        emit("sync");
        return;
    }
    emit("action", key);
};
</script>

<template>
    <div class="rail-detail-block">
        <Transition name="detail-crossfade" mode="out-in">
            <div
                v-if="device"
                :key="device.id"
                class="rail-detail-content"
            >
                <!-- 设备身份区 -->
                <div class="rail-device-head">
                    <span
                        class="rail-device-thumb"
                        :style="{ '--device-color': device.color || '#6b7280' }"
                        aria-hidden="true"
                    >
                        <SvgIcon :name="deviceIcon" />
                    </span>
                    <div class="rail-device-title">
                        <strong>{{ device.name }}</strong>
                        <small>{{ device.room }} · {{ device.brand }}</small>
                    </div>
                    <span class="rail-device-status" :class="`is-${device.status}`">
                        <i class="status-dot" :class="`is-${device.status}`"></i>
                        {{ deviceStatusLabelMap[device.status] }}
                    </span>
                </div>

                <!-- 基础信息 -->
                <dl class="rail-info-grid">
                    <div class="rail-info-item is-indigo">
                        <dt>
                            <span class="rail-info-icon">
                                <SvgIcon name="device-management" size="sm" />
                            </span>
                            类型
                        </dt>
                        <dd>{{ device.type }}</dd>
                    </div>
                    <div
                        class="rail-info-item"
                        :class="`is-${platformTone(device.connection)}`"
                    >
                        <dt>
                            <span class="rail-info-icon">
                                <SvgIcon name="platform" size="sm" />
                            </span>
                            接入平台
                        </dt>
                        <dd>{{ device.connection }}</dd>
                    </div>
                    <div class="rail-info-item is-purple">
                        <dt>
                            <span class="rail-info-icon">
                                <SvgIcon name="firmware" size="sm" />
                            </span>
                            固件版本
                        </dt>
                        <dd>{{ device.firmware || "—" }}</dd>
                    </div>
                    <div class="rail-info-item" :class="lastOnlineTone">
                        <dt>
                            <span class="rail-info-icon">
                                <SvgIcon name="clock" size="sm" />
                            </span>
                            最后在线
                        </dt>
                        <dd class="is-tabular">{{ formatLastOnline(device.lastOnline) }}</dd>
                    </div>
                </dl>
            </div>

            <div v-else key="empty" class="rail-detail-empty">
                <SvgIcon name="device-management" />
                <span>选择设备后查看详情</span>
            </div>
        </Transition>

        <DeviceRailActions
            v-if="device"
            :actions="detailActions"
            layout="row"
            :syncing-key="props.syncing ? 'sync' : ''"
            @action="handleAction"
        />
    </div>
</template>

<style scoped>
.rail-detail-block {
    display: grid;
    gap: 12px;
    padding: 14px;
}

.rail-detail-content {
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: var(--color-panel-background);
    box-shadow: var(--shadow-card);
}

.rail-device-head {
    display: grid;
    grid-template-columns: 48px minmax(0, 1fr) auto;
    align-items: center;
    gap: 10px;
    padding: 16px 16px 10px;
}

.rail-device-thumb {
    display: grid;
    width: 48px;
    height: 48px;
    place-items: center;
    border: 1px solid color-mix(in srgb, var(--device-color, var(--color-primary-500)) 18%, transparent);
    border-radius: 14px;
    background: color-mix(in srgb, var(--device-color, var(--color-primary-500)) 14%, transparent);
    color: var(--device-color, var(--color-primary-600));
}

.rail-device-title {
    min-width: 0;
    display: grid;
    gap: 2px;
}

.rail-device-title strong {
    overflow: hidden;
    font-size: 16px;
    font-weight: 900;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.rail-device-title small {
    overflow: hidden;
    font-size: 12px;
    color: var(--color-text-tertiary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.rail-device-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    align-self: start;
    border-radius: 999px;
    margin-top: 2px;
    padding: 4px 8px;
    background: var(--color-surface-subtle);
    font-size: 11px;
    font-weight: 800;
}

.rail-device-status.is-online { color: var(--color-success); background: var(--color-success-soft); }
.rail-device-status.is-warning { color: var(--color-warning); }
.rail-device-status.is-offline { color: var(--color-text-muted); }
.rail-device-status.is-running { color: var(--color-primary-600); }

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: currentColor;
}

.rail-info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 8px 14px 12px;
}

.rail-info-item {
    display: grid;
    gap: 3px;
    min-width: 0;
    padding: 8px 10px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--color-panel-secondary);
    transition: border-color 140ms ease;
}

.rail-info-item dt {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 800;
    color: var(--color-text-secondary);
}

.rail-info-item dd {
    margin: 0;
    overflow: hidden;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.rail-info-item dd.is-tabular {
    font-variant-numeric: tabular-nums;
}

.rail-info-icon {
    display: inline-grid;
    width: 16px;
    height: 16px;
    place-items: center;
    border-radius: 5px;
}

/* === 语义色调：浅色底 + 描边 + 彩色图标/数值 === */
.rail-info-item.is-indigo {
    border-color: color-mix(in srgb, var(--tone-indigo) 30%, transparent);
    background: color-mix(in srgb, var(--tone-indigo-soft) 42%, var(--color-panel-secondary));
}
.rail-info-item.is-indigo .rail-info-icon,
.rail-info-item.is-indigo dd { color: var(--tone-indigo); }

.rail-info-item.is-orange {
    border-color: color-mix(in srgb, var(--tone-orange) 30%, transparent);
    background: color-mix(in srgb, var(--tone-orange-soft) 42%, var(--color-panel-secondary));
}
.rail-info-item.is-orange .rail-info-icon,
.rail-info-item.is-orange dd { color: var(--tone-orange); }

.rail-info-item.is-purple {
    border-color: color-mix(in srgb, var(--tone-purple) 30%, transparent);
    background: color-mix(in srgb, var(--tone-purple-soft) 42%, var(--color-panel-secondary));
}
.rail-info-item.is-purple .rail-info-icon,
.rail-info-item.is-purple dd { color: var(--tone-purple); }

.rail-info-item.is-teal {
    border-color: color-mix(in srgb, var(--color-teal-600) 30%, transparent);
    background: color-mix(in srgb, var(--color-teal-soft) 45%, var(--color-panel-secondary));
}
.rail-info-item.is-teal .rail-info-icon,
.rail-info-item.is-teal dd { color: var(--color-teal-600); }

.rail-info-item.is-green {
    border-color: color-mix(in srgb, var(--color-success) 30%, transparent);
    background: color-mix(in srgb, var(--color-success-soft) 48%, var(--color-panel-secondary));
}
.rail-info-item.is-green .rail-info-icon,
.rail-info-item.is-green dd { color: var(--color-success); }

.rail-info-item.is-muted .rail-info-icon { color: var(--color-text-muted); }
.rail-info-item.is-muted dd { color: var(--color-text-tertiary); }

.rail-detail-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 28px 0;
    color: var(--color-text-muted);
    font-size: 13px;
    font-weight: 700;
}

.rail-detail-empty svg {
    width: 34px;
    height: 34px;
    opacity: 0.45;
}

/* 设备切换交叉淡入 */
.detail-crossfade-enter-active,
.detail-crossfade-leave-active {
    transition:
        opacity 160ms ease,
        transform 160ms var(--motion-ease);
}

.detail-crossfade-enter-from {
    opacity: 0;
    transform: translateY(4px);
}

.detail-crossfade-leave-to {
    opacity: 0;
}
</style>
