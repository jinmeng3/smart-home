<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { DeviceStatus, DeviceType } from "../../types/device";
import { deviceStatusOptions, deviceTypeOptions } from "./deviceMeta";

defineProps<{
    keyword: string;
    room: string;
    type: DeviceType | "";
    status: DeviceStatus | "";
    rooms: string[];
}>();

defineEmits<{
    "update:keyword": [value: string];
    "update:room": [value: string];
    "update:type": [value: DeviceType | ""];
    "update:status": [value: DeviceStatus | ""];
}>();
</script>

<template>
    <section class="device-toolbar">
        <label class="device-search">
            <input
                :value="keyword"
                placeholder="搜索设备、房间、品牌或类型"
                type="search"
                @input="$emit('update:keyword', ($event.target as HTMLInputElement).value)"
            />
            <span><SvgIcon name="search" /></span>
        </label>
        <select
            :value="room"
            @change="$emit('update:room', ($event.target as HTMLSelectElement).value)"
        >
            <option value="">房间</option>
            <option v-for="item in rooms" :key="item" :value="item">
                {{ item }}
            </option>
        </select>
        <select
            :value="type"
            @change="$emit('update:type', ($event.target as HTMLSelectElement).value as DeviceType | '')"
        >
            <option
                v-for="item in deviceTypeOptions"
                :key="item.label"
                :value="item.value"
            >
                {{ item.value ? item.label : "类型" }}
            </option>
        </select>
        <select
            :value="status"
            @change="$emit('update:status', ($event.target as HTMLSelectElement).value as DeviceStatus | '')"
        >
            <option
                v-for="item in deviceStatusOptions"
                :key="item.label"
                :value="item.value"
            >
                {{ item.value ? item.label : "状态" }}
            </option>
        </select>
    </section>
</template>

<style scoped>
.device-toolbar {
    display: grid;
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
    grid-template-columns: minmax(190px, 1fr) repeat(3, 96px);
    gap: 8px;
    align-items: center;
}

.device-toolbar-actions {
    display: contents;
    width: auto;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 6px;
}

.device-search {
    position: relative;
    min-width: 0;
}

.device-search input,
select {
    min-width: 0;
    width: 100%;
    height: 40px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 600;
    outline: none;
    transition:
        border-color 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease);
}

.device-search input {
    padding: 0 38px 0 14px;
}

select {
    padding: 0 12px;
}

.device-search span {
    position: absolute;
    right: 12px;
    top: 50%;
    color: var(--color-text-tertiary);
    transform: translateY(-50%);
}

.device-search input:focus,
select:focus {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.device-primary-button,
.device-secondary-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    height: 40px;
    border-radius: 8px;
    flex: 0 0 auto;
    min-width: 0;
    padding: 0 10px;
    font-size: 13px;
    font-weight: 800;
    white-space: nowrap;
    transition:
        transform 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

.device-primary-button {
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.device-secondary-button {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.device-secondary-button:not(:disabled):hover {
    border-color: var(--color-primary-200);
    color: var(--color-primary-700);
    background: var(--color-primary-50);
}

.device-sync-button svg {
    transition: transform 180ms var(--motion-ease);
}

.device-sync-button:disabled svg {
    animation: device-sync-spin 900ms linear infinite;
}

button:not(:disabled):hover {
    transform: translateY(-1px);
}

button:not(:disabled):active {
    transform: scale(0.98);
}

button:disabled {
    cursor: default;
    opacity: 0.55;
}

@media (max-width: 1600px) {
    .device-toolbar-actions {
        display: contents;
    }

    .device-primary-button,
    .device-secondary-button {
        padding: 0 8px;
        font-size: 12px;
    }
}

@media (max-width: 860px) {
    .device-toolbar {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .device-search {
        grid-column: 1 / -1;
    }

    .device-toolbar-actions {
        grid-column: 1 / -1;
        justify-self: end;
    }
}

@media (max-width: 560px) {
    .device-toolbar {
        grid-template-columns: 1fr;
    }

    .device-search {
        grid-column: auto;
    }

    .device-toolbar-actions {
        display: grid;
        width: 100%;
        grid-column: auto;
        grid-template-columns: 1fr;
    }
}

@keyframes device-sync-spin {
    to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
    .device-primary-button,
    .device-secondary-button,
    .device-search input,
    select {
        transition-duration: 1ms;
    }

    button:not(:disabled):hover,
    button:not(:disabled):active {
        transform: none;
    }
}
</style>
