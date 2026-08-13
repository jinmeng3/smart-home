<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Device } from "../../types/device";
import { deviceStatusLabelMap, deviceTypeIconMap, deviceTypeLabelMap, getDeviceTypeIcon, getDeviceTypeLabel } from "./deviceMeta";

defineProps<{
    device: Device | null;
}>();

const formatLastSync = (value: string): string => {
    if (!value) return "暂无";

    const time = new Date(value);
    if (Number.isNaN(time.getTime())) return value;

    const now = new Date();
    const diffMin = Math.floor((now.getTime() - time.getTime()) / 60000);
    const pad = (n: number) => String(n).padStart(2, "0");

    if (diffMin < 1) return "刚刚";
    if (diffMin < 60) return `${diffMin} 分钟前`;

    const clock = `${pad(time.getHours())}:${pad(time.getMinutes())}`;
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);

    if (time.toDateString() === now.toDateString()) return clock;
    if (time.toDateString() === yesterday.toDateString()) return `昨天 ${clock}`;
    if (time.getFullYear() === now.getFullYear()) {
        return `${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${clock}`;
    }
    return `${time.getFullYear()}-${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${clock}`;
};

const platformToneMap: Record<string, string> = {
    "Home Assistant": "orange",
    Matter: "blue",
    Zigbee: "green",
    MQTT: "purple",
};
</script>

<template>
    <section class="device-side-card">
        <header>
            <h2><SvgIcon name="device-management" size="sm" />设备详情</h2>
        </header>

        <Transition name="detail-crossfade" mode="out-in">
            <div :key="device ? device.id : 'empty'" class="detail-content">
                <div v-if="device" class="device-detail-body">
                    <div class="device-summary">
                        <div class="device-image" :style="{ '--device-color': device.color || '#6b7280' }">
                            <img v-if="device.image" :src="device.image" alt="" />
                            <span v-else>
                                <SvgIcon :name="getDeviceTypeIcon(device.icon || device.type)" size="lg" />
                            </span>
                        </div>
                        <div class="device-title">
                            <strong>{{ device.name }}</strong>
                            <span class="device-type">{{ getDeviceTypeLabel(device.type) }}</span>
                            <span class="device-status" :class="`is-${device.status}`">
                                <i :class="`status-dot is-${device.status}`"></i>
                                {{ deviceStatusLabelMap[device.status] }}
                            </span>
                        </div>
                    </div>
                    <dl>
                        <div>
                            <dt><SvgIcon name="room" size="sm" />房间</dt>
                            <dd class="is-room">{{ device.room }}</dd>
                        </div>
                        <div>
                            <dt><SvgIcon name="layers" size="sm" />品牌</dt>
                            <dd>{{ device.brand }}</dd>
                        </div>
                        <div>
                            <dt><SvgIcon name="plug" size="sm" />连接方式</dt>
                            <dd>
                                <em class="platform tone-chip" :class="`is-${platformToneMap[device.connection] ?? 'blue'}`">{{ device.connection }}</em>
                            </dd>
                        </div>
                        <div>
                            <dt><SvgIcon name="refresh" size="sm" />固件版本</dt>
                            <dd class="is-firmware">{{ device.firmware }}</dd>
                        </div>
                        <div>
                            <dt><SvgIcon name="clock" size="sm" />最后同步</dt>
                            <dd class="is-sync">{{ formatLastSync(device.lastOnline) }}</dd>
                        </div>
                    </dl>
                </div>

                <div v-else class="device-detail-empty">
                    <SvgIcon name="device-management" />
                    <span>选择设备后查看详情</span>
                </div>
            </div>
        </Transition>
    </section>
</template>

<style scoped>
.device-side-card {
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-panel-background);
    padding: 14px;
    box-shadow: var(--shadow-card);
}

.detail-crossfade-enter-active,
.detail-crossfade-leave-active {
    transition: opacity 140ms var(--motion-ease);
}
.detail-crossfade-enter-from,
.detail-crossfade-leave-to {
    opacity: 0;
}

header {
    display: flex;
    align-items: center;
}

h2 {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin: 0;
    font-size: 18px;
    font-weight: 900;
}

h2 svg {
    color: var(--color-primary-600);
}

.device-detail-body {
    display: grid;
    gap: 14px;
    margin-top: 14px;
}

.device-summary {
    display: grid;
    grid-template-columns: 76px minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--color-border);
}

.device-image {
    display: grid;
    width: 76px;
    height: 76px;
    place-items: center;
    border-radius: 14px;
    background: color-mix(in srgb, var(--device-color, #6b7280) 16%, transparent);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--device-color, #6b7280) 18%, transparent);
    color: var(--device-color, #6b7280);
}

.device-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.device-image span {
    color: var(--device-color, #6b7280);
    font-size: 28px;
    font-weight: 900;
}

.device-title {
    display: grid;
    min-width: 0;
    gap: 5px;
}

.device-title strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-type {
    width: fit-content;
    border-radius: 999px;
    background: var(--color-primary-50);
    padding: 2px 9px;
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 800;
}

.device-status {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-default);
    border-radius: 999px;
    background: var(--color-surface-subtle);
    padding: 4px 10px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    --status-dot-size: 8px;
}

.device-status.is-online {
    border-color: var(--color-success-border);
    background: var(--color-success-soft);
    color: var(--color-success);
}

.device-status.is-running {
    border-color: var(--color-info-border);
    background: var(--color-info-soft);
    color: var(--color-info);
}

.device-status.is-warning {
    border-color: var(--color-warning-border);
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

dl {
    display: grid;
    gap: 0;
    margin: 0;
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-surface-subtle);
}

dl div {
    display: flex;
    min-width: 0;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 12px;
    transition: background 160ms var(--motion-ease);
}

dl div + div {
    border-top: 1px solid var(--color-border-subtle);
}

dl div:hover {
    background: var(--color-card-bg);
}

dt {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    flex: 0 0 auto;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 750;
}

.dl-row svg,
dt svg {
    flex: 0 0 auto;
}

dl div:nth-child(1) dt svg {
    color: var(--color-primary-600);
}

dl div:nth-child(2) dt svg {
    color: var(--color-success);
}

dl div:nth-child(3) dt svg {
    color: var(--color-warning);
}

dl div:nth-child(4) dt svg {
    color: var(--tone-purple);
}

dl div:nth-child(5) dt svg {
    color: var(--color-info);
}

dd {
    overflow: hidden;
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    text-align: right;
    text-overflow: ellipsis;
    white-space: nowrap;
}

dd.is-room {
    color: var(--color-primary-700);
}

dd.is-firmware {
    color: var(--tone-purple);
}

dd.is-sync {
    color: var(--color-info);
}

dd .platform {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 12px;
    font-style: normal;
    font-weight: 900;
}

.device-detail-empty {
    display: grid;
    min-height: 160px;
    place-items: center;
    align-content: center;
    gap: 10px;
    color: var(--color-text-tertiary);
    font-weight: 700;
}

.device-detail-empty svg {
    width: 40px;
    height: 40px;
    color: var(--color-text-muted);
}

@keyframes side-card-enter {
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
    .device-side-card {
        animation-duration: 1ms;
        animation-iteration-count: 1;
    }
    dl div {
        transition-duration: 1ms;
    }
}
</style>
