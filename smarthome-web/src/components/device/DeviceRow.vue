<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import { formatDeviceTimestamp } from "../../utils/device";
import type { Device } from "../../types/device";
import {
    deviceStatusLabelMap,
    deviceTypeIconMap,
    deviceTypeLabelMap,
    getDeviceTypeIcon,
    getDeviceTypeLabel,
    getStatusClasses,
} from "./deviceMeta";

defineProps<{
    device: Device;
    selected: boolean;
    batchMode?: boolean;
    batchSelected?: boolean;
}>();

defineEmits<{
    select: [device: Device];
    "batch-select": [device: Device];
    edit: [device: Device];
    remove: [device: Device];
}>();
</script>

<template>
    <tr
        class="device-row"
        :data-flip-id="`dev-${device.id}`"
        :class="{ 'is-selected': selected }"
        @click="$emit('select', device)"
    >
        <td>
            <input
                class="device-checkbox"
                :checked="batchMode ? batchSelected : selected"
                type="checkbox"
                @click.stop="batchMode ? $emit('batch-select', device) : $emit('select', device)"
            />
        </td>
        <td>
            <div class="device-name-cell">
                <span
                    class="device-thumb"
                    :style="{ '--device-color': device.color || '#6b7280' }"
                    aria-hidden="true"
                >
                    <SvgIcon :name="getDeviceTypeIcon(device.icon || device.type)" size="sm" />
                </span>
                <strong>{{ device.name }}</strong>
            </div>
        </td>
        <td>{{ device.room }}</td>
        <td>{{ getDeviceTypeLabel(device.type) }}</td>
        <td>{{ device.brand }}</td>
        <td>
            <span
                class="device-status-badge"
                :class="getStatusClasses(device.status)"
            >
                <i :class="`status-dot is-${device.status}`"></i>
                {{ deviceStatusLabelMap[device.status] }}
            </span>
        </td>
        <td>{{ formatDeviceTimestamp(device.lastOnline, "从未在线") }}</td>
        <td>
            <div class="device-row-actions">
                <button type="button" @click.stop="$emit('edit', device)">
                    编辑
                </button>
                <button type="button" @click.stop="$emit('remove', device)">
                    删除
                </button>
            </div>
        </td>
    </tr>
</template>

<style scoped>
.device-row {
    cursor: pointer;
    transition:
        background-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.device-row:hover {
    background: var(--color-surface-hover);
}

.device-row.is-selected {
    background: var(--color-primary-50);
    box-shadow: inset 3px 0 0 var(--color-primary-600);
}

/* 设备行固定列宽 */
.device-row td:first-child {
    width: 16px;
    padding-right: 4px;
}

.device-row td:nth-child(2) {
    min-width: 180px;
}

.device-row td:nth-child(3) {
    width: 100px;
}

.device-row td:nth-child(4) {
    width: 90px;
}

.device-row td:nth-child(5) {
    width: 120px;
}

.device-row td:nth-child(6) {
    width: 100px;
}

.device-row td:nth-child(7) {
    width: 130px;
}

.device-row td:nth-child(8) {
    width: 120px;
}

.device-row td {
    overflow: hidden;
    border-top: 1px solid var(--color-border-subtle);
    padding: 12px 10px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-name-cell {
    display: grid;
    grid-template-columns: 34px minmax(0, 1fr);
    align-items: center;
    gap: 10px;
}

.device-name-cell strong {
    overflow: hidden;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
}

.device-thumb {
    display: grid;
    width: 34px;
    height: 28px;
    place-items: center;
    border-radius: 7px;
    background: color-mix(in srgb, var(--device-color, #6b7280) 14%, transparent);
    color: var(--device-color, #6b7280);
    flex-shrink: 0;
}

.device-checkbox {
    width: 16px;
    height: 16px;
    accent-color: var(--color-primary-600);
}

.device-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid;
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 13px;
    font-weight: 900;
}

.device-row-actions {
    display: flex;
    gap: 8px;
    white-space: nowrap;
}

.device-row-actions button {
    flex: 0 0 auto;
    border: 0;
    background: transparent;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
    transition:
        color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.device-row-actions button:hover {
    color: var(--color-primary-800);
    transform: translateY(-1px);
}

@media (prefers-reduced-motion: reduce) {
    .device-row:hover,
    .device-row.is-selected {
        transform: none;
    }
}
</style>
