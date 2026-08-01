<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Device, DeviceType } from "../../types/device";
import DeviceRow from "./DeviceRow.vue";
import { deviceTypeOptions } from "./deviceMeta";

defineProps<{
    devices: Device[];
    total: number;
    page: number;
    pageSize: number;
    selectedId: number | null;
    loading: boolean;
    sort: "updated" | "name" | "status";
    activeType: DeviceType | "";
}>();

defineEmits<{
    "update:page": [value: number];
    "update:pageSize": [value: number];
    "update:sort": [value: "updated" | "name" | "status"];
    "update:activeType": [value: DeviceType | ""];
    select: [device: Device];
    edit: [device: Device];
    remove: [device: Device];
}>();

const pageSizeOptions = [10, 20, 50];
</script>

<template>
    <section class="device-list-panel">
        <header class="device-list-header">
            <h2>设备列表</h2>
            <div class="device-list-tools">
                <select
                    :value="sort"
                    @change="$emit('update:sort', ($event.target as HTMLSelectElement).value as 'updated' | 'name' | 'status')"
                >
                    <option value="updated">按最后在线</option>
                    <option value="name">按名称</option>
                    <option value="status">按状态</option>
                </select>
                <button class="is-active" type="button" title="列表视图">
                    <SvgIcon name="list" />
                </button>
                <button type="button" title="网格视图">
                    <SvgIcon name="grid" />
                </button>
            </div>
        </header>

        <div class="device-type-tabs">
            <button
                v-for="item in deviceTypeOptions"
                :key="item.label"
                :class="{ 'is-active': activeType === item.value }"
                type="button"
                @click="$emit('update:activeType', item.value)"
            >
                {{ item.label }}
            </button>
        </div>

        <div class="device-table-wrap">
            <table>
                <thead>
                    <tr>
                        <th></th>
                        <th>设备名称</th>
                        <th>房间</th>
                        <th>类型</th>
                        <th>品牌</th>
                        <th>状态</th>
                        <th>最后在线</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody v-if="!loading && devices.length">
                    <DeviceRow
                        v-for="device in devices"
                        :key="device.id"
                        :device="device"
                        :selected="selectedId === device.id"
                        @edit="$emit('edit', $event)"
                        @remove="$emit('remove', $event)"
                        @select="$emit('select', $event)"
                    />
                </tbody>
            </table>
            <div v-if="loading" class="device-empty">正在加载设备</div>
            <div v-else-if="!devices.length" class="device-empty">
                暂无设备数据
            </div>
        </div>

        <footer class="device-pagination">
            <span>共 {{ total }} 条</span>
            <div class="device-page-actions">
                <button
                    :disabled="page <= 1"
                    type="button"
                    @click="$emit('update:page', page - 1)"
                >
                    ‹
                </button>
                <strong>{{ page }}</strong>
                <button
                    :disabled="page * pageSize >= total"
                    type="button"
                    @click="$emit('update:page', page + 1)"
                >
                    ›
                </button>
            </div>
            <select
                :value="pageSize"
                @change="$emit('update:pageSize', Number(($event.target as HTMLSelectElement).value))"
            >
                <option v-for="item in pageSizeOptions" :key="item" :value="item">
                    {{ item }} 条/页
                </option>
            </select>
        </footer>
    </section>
</template>

<style scoped>
.device-list-panel {
    display: flex;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 16px;
    box-shadow: var(--shadow-card);
    animation: device-list-enter 240ms var(--motion-ease) both;
}

.device-list-header,
.device-list-tools,
.device-type-tabs,
.device-pagination,
.device-page-actions {
    display: flex;
    align-items: center;
}

.device-list-header {
    justify-content: space-between;
    gap: 16px;
}

.device-list-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 900;
}

.device-list-tools,
.device-type-tabs,
.device-page-actions {
    gap: 8px;
}

.device-list-tools select,
.device-pagination select {
    height: 38px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    color: var(--color-text-secondary);
    font-weight: 700;
}

.device-list-tools button,
.device-type-tabs button,
.device-page-actions button,
.device-page-actions strong {
    min-width: 34px;
    height: 34px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    color: var(--color-text-secondary);
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

.device-type-tabs {
    margin: 14px 0;
    flex-wrap: wrap;
}

.device-type-tabs button {
    min-width: auto;
    padding: 0 12px;
    font-size: 12px;
}

.device-list-tools .is-active,
.device-type-tabs .is-active,
.device-page-actions strong {
    border-color: var(--color-primary-500);
    background: var(--color-primary-600);
    color: #fff;
}

.device-table-wrap {
    min-height: 0;
    flex: 1;
    overflow: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

th {
    padding: 10px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 900;
    text-align: left;
    white-space: nowrap;
}

th:first-child {
    width: 42px;
}

th:nth-child(2) {
    width: 24%;
}

th:last-child {
    width: 118px;
}

.device-empty {
    display: grid;
    min-height: 220px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-weight: 700;
}

.device-pagination {
    justify-content: space-between;
    gap: 14px;
    padding-top: 14px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

button:not(:disabled):hover {
    transform: translateY(-1px);
}

button:not(:disabled):active {
    transform: scale(0.98);
}

button:disabled {
    cursor: default;
    opacity: 0.45;
}

@keyframes device-list-enter {
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
    .device-list-panel,
    button {
        animation-duration: 1ms;
        transition-duration: 1ms;
    }

    button:not(:disabled):hover,
    button:not(:disabled):active {
        transform: none;
    }
}
</style>
