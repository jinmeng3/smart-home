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
    syncing: boolean;
}>();

defineEmits<{
    "update:keyword": [value: string];
    "update:room": [value: string];
    "update:type": [value: DeviceType | ""];
    "update:status": [value: DeviceStatus | ""];
    add: [];
    batch: [];
    sync: [];
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
        <button class="device-primary-button" type="button" @click="$emit('add')">
            <SvgIcon name="plus" /> 添加设备
        </button>
        <button class="device-secondary-button" type="button" @click="$emit('batch')">
            <SvgIcon name="layers" /> 批量操作
        </button>
        <button
            class="device-secondary-button"
            :disabled="syncing"
            type="button"
            @click="$emit('sync')"
        >
            <SvgIcon name="refresh" /> {{ syncing ? "同步中" : "同步设备" }}
        </button>
    </section>
</template>

<style scoped>
.device-toolbar {
    display: grid;
    grid-template-columns: minmax(240px, 1fr) 112px 112px 112px auto auto auto;
    gap: 10px;
    align-items: center;
}

.device-search {
    position: relative;
    min-width: 0;
}

.device-search input,
select {
    width: 100%;
    height: 40px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
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
    padding: 0 16px;
    font-size: 14px;
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
    color: #fff;
    box-shadow: 0 10px 20px rgb(37 99 235 / 18%);
}

.device-secondary-button {
    border: 1px solid var(--color-border-default);
    background: var(--color-panel-background);
    color: var(--color-text-secondary);
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

@media (max-width: 1280px) {
    .device-toolbar {
        grid-template-columns: minmax(220px, 1fr) repeat(3, 104px);
    }
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
