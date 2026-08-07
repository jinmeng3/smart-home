<script setup lang="ts">
import { computed } from "vue";
import { useHomeStore } from "../../stores/home";
import type { DashboardDevice } from "../../types/device";
import SvgIcon from "../common/SvgIcon.vue";
import {
    deviceTypeIconMap,
    getDeviceStatusLabel,
    getDeviceTypeIcon,
} from "../device/deviceMeta";
import { formatDeviceTimestamp } from "../../utils/device";
import { isLoading } from "../../types/loading";

const store = useHomeStore();

const visibleDevices = computed(() => store.devices.slice(0, 6));

const statusLabel = (device: DashboardDevice) =>
    getDeviceStatusLabel(device.status);
</script>

<template>
    <section
        class="motion-card rounded-lg border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
    >
        <div class="mb-3 flex items-center justify-between gap-3">
            <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                当前设备
            </h2>
            <span class="text-xs font-bold text-[var(--color-text-tertiary)]">
                {{ store.deviceSummary.online }}/{{
                    store.deviceSummary.total
                }}
                在线
            </span>
        </div>

        <div v-if="isLoading(store.devicesLoading)" class="device-placeholder">
            正在加载设备
        </div>

        <div v-else-if="!visibleDevices.length" class="device-placeholder">
            暂无设备
        </div>

        <div v-else class="grid gap-2">
            <article
                v-for="device in visibleDevices"
                :key="device.id"
                class="device-row"
                :class="`is-${device.status}`"
            >
                <span
                    class="device-icon"
                    :class="`is-${device.type}`"
                    aria-hidden="true"
                >
                    <SvgIcon :name="getDeviceTypeIcon(device.icon || device.type)" size="sm" />
                </span>
                <div class="device-copy">
                    <strong>{{ device.name }}</strong>
                    <small
                        >{{ device.room }} ·
                        {{ formatDeviceTimestamp(device.updatedAt) }}</small
                    >
                </div>
                <span class="device-status">
                    {{ device.value ?? statusLabel(device) }}
                </span>
            </article>
        </div>
    </section>
</template>

<style scoped>
.device-row {
    display: grid;
    min-width: 0;
    grid-template-columns: 28px minmax(0, 1fr) minmax(56px, auto);
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid var(--color-border-subtle);
    padding: 7px 0;
}

.device-row:last-child {
    border-bottom: 0;
}

.device-icon {
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    color: var(--color-primary-700);
}

.device-icon.is-light {
    background: var(--color-warning-soft);
    color: var(--color-device-light);
}

.device-icon.is-air_conditioner {
    background: var(--color-info-soft);
    color: var(--color-device-climate);
}

.device-icon.is-lock {
    background: var(--color-surface-subtle);
    color: var(--color-device-lock);
}

.device-icon.is-camera {
    background: var(--color-device-camera-soft);
    color: var(--color-device-camera);
}

.device-icon.is-sensor {
    background: var(--color-success-soft);
    color: var(--color-device-air);
}

.device-icon.is-socket {
    background: var(--color-teal-soft);
    color: var(--color-device-energy);
}

.device-icon.is-curtain {
    background: var(--color-teal-soft);
    color: var(--color-teal-600);
}

.device-copy {
    display: grid;
    min-width: 0;
    gap: 2px;
}

.device-copy strong,
.device-copy small,
.device-status {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-copy strong {
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 800;
}

.device-copy small {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
}

.device-status {
    border-radius: 999px;
    background: var(--color-surface-subtle);
    padding: 4px 8px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
    text-align: center;
}

.device-row.is-online .device-status,
.device-row.is-running .device-status {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.device-row.is-warning .device-status {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.device-row.is-offline .device-status {
    color: var(--color-text-tertiary);
}

.device-placeholder {
    display: grid;
    min-height: 132px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}
</style>
