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
            <SvgIcon name="search" size="sm" />
            <input
                :value="keyword"
                placeholder="搜索设备、房间、品牌或类型"
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
            <SvgIcon name="room" size="sm" />
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
            <SvgIcon name="layers" size="sm" />
            <select
                :value="type"
                @change="
                    $emit(
                        'update:type',
                        ($event.target as HTMLSelectElement).value as
                            DeviceType | '',
                    )
                "
            >
                <option
                    v-for="item in deviceTypeOptions"
                    :key="item.label"
                    :value="item.value"
                >
                    {{ item.value ? item.label : "全部类型" }}
                </option>
            </select>
            <SvgIcon class="dropdown-arrow" name="chevron-down" size="sm" />
        </div>
        <div class="filter-group">
            <SvgIcon name="list" size="sm" />
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
    </section>
</template>

<style scoped>
.device-toolbar {
    display: grid;
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
    grid-template-columns: minmax(180px, 1fr) repeat(3, 120px);
    gap: 8px;
    align-items: center;
}

/* ── 搜索框 ── */
.device-search {
    position: relative;
    display: flex;
    align-items: center;
    gap: 8px;
    height: 40px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0 12px;
    transition: border-color 180ms var(--motion-ease), box-shadow 180ms var(--motion-ease);
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
    font-weight: 600;
}

/* ── 筛选下拉框 ── */
.filter-group {
    position: relative;
    display: flex;
    align-items: center;
    gap: 6px;
    height: 40px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
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
    flex: 1;
    min-width: 0;
    border: none;
    background: none;
    padding: 0;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 700;
    outline: none;
    appearance: none;
    cursor: pointer;
}

.filter-group select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.dropdown-arrow {
    pointer-events: none;
    color: var(--color-text-tertiary);
}

/* ── 响应式 ── */
@media (max-width: 1100px) {
    .device-toolbar {
        grid-template-columns: 1fr 1fr;
    }
    .device-search {
        grid-column: 1 / -1;
    }
}

@media (max-width: 560px) {
    .device-toolbar {
        grid-template-columns: 1fr;
    }
}
</style>