<script setup lang="ts">
import { computed } from "vue";
import { useHomeStore } from "../../stores/home";
import type { DashboardDevice } from "../../types/device";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();

const visibleDevices = computed(() => store.devices.slice(0, 6));

const statusLabelMap: Record<string, string> = {
    online: "在线",
    offline: "离线",
    running: "运行中",
    warning: "告警",
};

const iconNameMap: Record<DashboardDevice["type"], string> = {
    light: "light",
    air_conditioner: "air-conditioner",
    lock: "lock",
    camera: "camera",
    sensor: "sensor",
    socket: "plug",
    curtain: "curtain",
};

const formatUpdatedAt = (value: string) => {
    const match = value.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);

    if (match) {
        return `${match[1]} ${match[2]}`;
    }

    return value;
};

const statusLabel = (device: DashboardDevice) =>
    statusLabelMap[device.status] ?? device.status;
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

        <div v-if="store.devicesLoading" class="device-placeholder">
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
                <span class="device-icon" aria-hidden="true">
                    <SvgIcon :name="iconNameMap[device.type]" size="sm" />
                </span>
                <div class="device-copy">
                    <strong>{{ device.name }}</strong>
                    <small
                        >{{ device.room }} ·
                        {{ formatUpdatedAt(device.updatedAt) }}</small
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
