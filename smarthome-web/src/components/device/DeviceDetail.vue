<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Device } from "../../types/device";
import { deviceStatusLabelMap, deviceTypeLabelMap } from "./deviceMeta";

defineProps<{
    device: Device | null;
}>();

const iconNameMap: Record<Device["type"], string> = {
    light: "light",
    air_conditioner: "air-conditioner",
    lock: "lock",
    camera: "camera",
    sensor: "sensor",
    socket: "plug",
    curtain: "curtain",
};
</script>

<template>
    <section class="device-side-card">
        <header>
            <h2>设备详情</h2>
            <button type="button" title="更多"><SvgIcon name="more" /></button>
        </header>

        <div v-if="device" class="device-detail-body">
            <div class="device-image">
                <img v-if="device.image" :src="device.image" alt="" />
                <span v-else>
                    <SvgIcon :name="iconNameMap[device.type]" size="lg" />
                </span>
            </div>
            <div class="device-title">
                <i :class="`status-dot is-${device.status}`"></i>
                <strong>{{ device.name }}</strong>
                <small>{{ deviceStatusLabelMap[device.status] }}</small>
            </div>
            <dl>
                <div>
                    <dt>房间</dt>
                    <dd>{{ device.room }}</dd>
                </div>
                <div>
                    <dt>品牌</dt>
                    <dd>{{ device.brand }}</dd>
                </div>
                <div>
                    <dt>连接方式</dt>
                    <dd>{{ device.connection }}</dd>
                </div>
                <div>
                    <dt>固件版本</dt>
                    <dd>{{ device.firmware }}</dd>
                </div>
                <div>
                    <dt>最后同步</dt>
                    <dd>{{ device.lastOnline || "暂无" }}</dd>
                </div>
            </dl>
        </div>

        <div v-else class="device-detail-empty">
            选择设备后查看详情
        </div>
    </section>
</template>

<style scoped>
.device-side-card {
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 14px;
    box-shadow: var(--shadow-card);
    animation: side-card-enter 220ms var(--motion-ease) both;
}

header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

h2 {
    margin: 0;
    font-size: 16px;
    font-weight: 900;
}

header button {
    border: 0;
    background: transparent;
    color: var(--color-text-tertiary);
    font-size: 22px;
}

.device-detail-body {
    display: grid;
    grid-template-columns: 88px minmax(0, 1fr);
    gap: 14px;
    margin-top: 14px;
}

.device-image {
    display: grid;
    width: 88px;
    height: 92px;
    place-items: center;
    border-radius: 8px;
    background: linear-gradient(180deg, var(--color-card-bg), var(--color-primary-50));
    overflow: hidden;
}

.device-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.device-image span {
    color: var(--color-primary-700);
    font-size: 28px;
    font-weight: 900;
}

.device-title {
    display: grid;
    grid-template-columns: 10px minmax(0, 1fr);
    gap: 8px;
    align-content: start;
    align-items: center;
}

.device-title strong {
    overflow: hidden;
    font-size: 15px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-title small {
    grid-column: 2;
    color: var(--color-text-tertiary);
    font-weight: 700;
}

dl {
    grid-column: 2;
    display: grid;
    gap: 10px;
    margin: -50px 0 0;
}

dl div {
    display: flex;
    justify-content: space-between;
    gap: 12px;
}

dt {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

dd {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    text-align: right;
}

.device-detail-empty {
    display: grid;
    min-height: 160px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-weight: 700;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
}

.status-dot.is-online { background: var(--color-success); animation: pulse 1800ms var(--motion-ease) infinite; }
.status-dot.is-offline { background: var(--color-text-muted); }
.status-dot.is-running { background: var(--color-info); animation: pulse 1500ms var(--motion-ease) infinite; }
.status-dot.is-warning { background: var(--color-warning); animation: pulse 1100ms var(--motion-ease) infinite; }

@keyframes side-card-enter {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0%, 100% { opacity: 0.7; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.45); }
}

@media (prefers-reduced-motion: reduce) {
    .device-side-card,
    .status-dot {
        animation-duration: 1ms;
        animation-iteration-count: 1;
    }
}
</style>
