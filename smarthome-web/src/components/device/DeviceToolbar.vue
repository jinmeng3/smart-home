<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { DeviceStatus } from "../../types/device";
import { deviceStatusOptions } from "./deviceMeta";

defineProps<{
    keyword: string;
    room: string;
    status: DeviceStatus | "";
    rooms: string[];
}>();

defineEmits<{
    add: [];
    "update:keyword": [value: string];
    "update:room": [value: string];
    "update:status": [value: DeviceStatus | ""];
}>();
</script>

<template>
    <section class="device-toolbar">
        <label class="device-search">
            <SvgIcon name="search" size="sm" />
            <input
                :value="keyword"
                placeholder="搜索设备"
                type="search"
                @input="
                    $emit(
                        'update:keyword',
                        ($event.target as HTMLInputElement).value,
                    )
                "
            />
        </label>
        <div class="filter-group">
            <select
                :value="room"
                @change="
                    $emit('update:room', ($event.target as HTMLSelectElement).value)
                "
            >
                <option value="">全部房间</option>
                <option v-for="item in rooms" :key="item" :value="item">
                    {{ item }}
                </option>
            </select>
            <SvgIcon class="dropdown-arrow" name="chevron-down" size="sm" />
        </div>
        <div class="filter-group">
            <select
                :value="status"
                @change="
                    $emit(
                        'update:status',
                        ($event.target as HTMLSelectElement).value as
                            DeviceStatus | '',
                    )
                "
            >
                <option
                    v-for="item in deviceStatusOptions"
                    :key="item.label"
                    :value="item.value"
                >
                    {{ item.value ? item.label : "全部状态" }}
                </option>
            </select>
            <SvgIcon class="dropdown-arrow" name="chevron-down" size="sm" />
        </div>
        <button class="device-add-button" type="button" @click="$emit('add')">
            <SvgIcon name="plus" size="sm" />
            添加设备
        </button>
    </section>
</template>

<style scoped>
.device-toolbar {
    display: grid;
    width: min(100%, 688px);
    min-width: 0;
    margin-left: auto;
    box-sizing: border-box;
    grid-template-columns: minmax(260px, 290px) 126px 126px 116px;
    gap: 8px;
    align-items: center;
}

/* ── 搜索框 ── */
.device-search {
    position: relative;
    display: flex;
    align-items: center;
    gap: 6px;
    height: 34px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 9px;
    transition: border-color 180ms var(--motion-ease), box-shadow 180ms var(--motion-ease);
}

.device-add-button {
    display: inline-flex;
    height: 34px;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid var(--color-primary-600);
    border-radius: 8px;
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    font-size: 11px;
    font-weight: 800;
    white-space: nowrap;
    box-shadow: none;
    transition:
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.device-add-button:hover {
    border-color: var(--color-primary-700);
    background: var(--color-primary-700);
    box-shadow: 0 6px 14px var(--color-focus-ring);
    transform: translateY(-1px);
}

.device-add-button:active {
    transform: scale(0.98);
}

.device-search:focus-within {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.device-search > svg {
    flex-shrink: 0;
    color: var(--color-text-tertiary);
}

.device-search input {
    flex: 1;
    min-width: 0;
    border: none;
    background: none;
    padding: 0;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 600;
    outline: none;
}

.device-search input::placeholder {
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 600;
}

/* ── 筛选下拉框 ── */
.filter-group {
    position: relative;
    display: flex;
    align-items: center;
    gap: 6px;
    height: 34px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
    transition: border-color 180ms var(--motion-ease), box-shadow 180ms var(--motion-ease);
}

.filter-group:focus-within {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.filter-group > svg {
    flex-shrink: 0;
    color: var(--color-text-tertiary);
}

.filter-group select {
    width: 100%;
    height: 100%;
    min-width: 0;
    border: 0;
    border-radius: 0;
    background: transparent;
    background-image: none;
    padding: 0 24px 0 0 !important;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 700;
    box-shadow: none;
    outline: none;
    appearance: none;
    cursor: pointer;
    transform: none;
}

.filter-group select:hover,
.filter-group select:focus,
.filter-group select:focus-visible {
    border: 0;
    background: transparent;
    box-shadow: none;
    transform: none;
}

.filter-group select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.dropdown-arrow {
    position: absolute;
    right: 10px;
    pointer-events: none;
    color: var(--color-text-tertiary);
}

/* ── 响应式 ── */
@media (max-width: 900px) {
    .device-toolbar {
        width: 100%;
        grid-template-columns: minmax(200px, 1fr) repeat(2, 126px) 116px;
    }
}

@media (max-width: 720px) {
    .device-toolbar {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .device-search {
        grid-column: 1 / -1;
    }
}

@media (max-width: 560px) {
    .device-toolbar {
        width: 100%;
        grid-template-columns: 1fr;
    }

    .device-search {
        grid-column: auto;
    }
}
</style>
