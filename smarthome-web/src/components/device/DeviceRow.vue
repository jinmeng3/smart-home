<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Device } from "../../types/device";
import {
    deviceStatusLabelMap,
    deviceTypeLabelMap,
    getStatusClasses,
} from "./deviceMeta";

defineProps<{
    device: Device;
    selected: boolean;
}>();

defineEmits<{
    select: [device: Device];
    edit: [device: Device];
    remove: [device: Device];
}>();

const formatLastOnline = (value: string) => value || "从未在线";
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
    <tr
        class="device-row"
        :class="{ 'is-selected': selected }"
        @click="$emit('select', device)"
    >
        <td>
            <input
                class="device-checkbox"
                :checked="selected"
                type="checkbox"
                @click.stop="$emit('select', device)"
            />
        </td>
        <td>
            <div class="device-name-cell">
                <span class="device-thumb" aria-hidden="true">
                    <SvgIcon :name="iconNameMap[device.type]" size="sm" />
                </span>
                <strong>{{ device.name }}</strong>
            </div>
        </td>
        <td>{{ device.room }}</td>
        <td>{{ deviceTypeLabelMap[device.type] }}</td>
        <td>{{ device.brand }}</td>
        <td>
            <span class="device-status-badge" :class="getStatusClasses(device.status)">
                <i :class="`status-dot is-${device.status}`"></i>
                {{ deviceStatusLabelMap[device.status] }}
            </span>
        </td>
        <td>{{ formatLastOnline(device.lastOnline) }}</td>
        <td>
            <div class="device-row-actions">
                <button type="button" @click.stop="$emit('select', device)">详情</button>
                <button type="button" @click.stop="$emit('edit', device)">编辑</button>
                <button type="button" @click.stop="$emit('remove', device)">删除</button>
            </div>
        </td>
    </tr>
</template>

<style scoped>
.device-row {
    animation: device-row-enter 220ms var(--motion-ease) both;
    cursor: pointer;
    transition:
        opacity 180ms var(--motion-ease),
        transform 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease),
        background-color 180ms var(--motion-ease);
}

.device-row:hover,
.device-row.is-selected {
    background: var(--color-surface-hover);
    box-shadow: 0 8px 18px rgb(37 99 235 / 8%);
    transform: translateY(-2px);
}

.device-row td {
    border-top: 1px solid var(--color-border-subtle);
    padding: 12px 10px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 600;
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
    background: linear-gradient(180deg, #fff, var(--color-primary-50));
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 900;
    box-shadow: inset 0 0 0 1px var(--color-border-subtle);
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
    font-size: 12px;
    font-weight: 900;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 999px;
}

.status-dot.is-online {
    background: var(--color-success);
    animation: device-status-breathe 1800ms var(--motion-ease) infinite;
}

.status-dot.is-offline {
    background: var(--color-text-muted);
}

.status-dot.is-running {
    background: var(--color-info);
    animation: device-status-blink 1500ms var(--motion-ease) infinite;
}

.status-dot.is-warning {
    background: var(--color-warning);
    animation: device-status-alert 1100ms var(--motion-ease) infinite;
}

.device-row-actions {
    display: flex;
    gap: 8px;
}

.device-row-actions button {
    border: 0;
    background: transparent;
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 900;
    transition:
        color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.device-row-actions button:hover {
    color: var(--color-primary-800);
    transform: translateY(-1px);
}

@keyframes device-row-enter {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes device-status-breathe {
    0%, 100% { opacity: 0.65; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.45); }
}

@keyframes device-status-blink {
    0%, 100% { opacity: 0.55; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.25); }
}

@keyframes device-status-alert {
    0%, 100% { opacity: 0.7; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.5); }
}

@media (prefers-reduced-motion: reduce) {
    .device-row,
    .status-dot,
    .device-row-actions button {
        animation-duration: 1ms;
        animation-iteration-count: 1;
        transition-duration: 1ms;
    }

    .device-row:hover,
    .device-row.is-selected,
    .device-row-actions button:hover {
        transform: none;
    }
}
</style>
