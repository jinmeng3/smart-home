<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Device } from "../../types/device";
import { deviceStatusLabelMap, deviceTypeIconMap, deviceTypeLabelMap } from "./deviceMeta";

defineProps<{
    device: Device | null;
}>();
</script>

<template>
    <section class="device-side-card">
        <header>
            <h2>设备详情</h2>
        </header>

        <div v-if="device" class="device-detail-body">
            <div class="device-summary">
                <div class="device-image">
                    <img v-if="device.image" :src="device.image" alt="" />
                    <span v-else>
                        <SvgIcon :name="deviceTypeIconMap[device.type]" size="lg" />
                    </span>
                </div>
                <div class="device-title">
                    <strong>{{ device.name }}</strong>
                    <span class="device-type">{{
                        deviceTypeLabelMap[device.type]
                    }}</span>
                    <span class="device-status">
                        <i :class="`status-dot is-${device.status}`"></i>
                        {{ deviceStatusLabelMap[device.status] }}
                    </span>
                </div>
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

        <div v-else class="device-detail-empty">选择设备后查看详情</div>
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
}

h2 {
    margin: 0;
    font-size: 16px;
    font-weight: 900;
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
}

.device-image {
    display: grid;
    width: 76px;
    height: 76px;
    place-items: center;
    border-radius: 8px;
    background: linear-gradient(
        180deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
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
    min-width: 0;
    gap: 6px;
}

.device-title strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-type {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.device-status {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-default);
    border-radius: 999px;
    background: var(--color-surface-subtle);
    padding: 4px 9px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    --status-dot-size: 8px;
}

dl {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin: 0;
}

dl div {
    min-width: 0;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 10px;
}

dt {
    margin-bottom: 5px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

dd {
    overflow: hidden;
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

dl div:last-child {
    grid-column: 1 / -1;
}

.device-detail-empty {
    display: grid;
    min-height: 160px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-weight: 700;
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
}
</style>
