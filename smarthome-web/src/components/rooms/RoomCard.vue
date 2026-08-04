<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Room, RoomDeviceCard } from "../../types/room";

defineProps<{
    room: Room;
    selected: boolean;
    devices: RoomDeviceCard[];
}>();

defineEmits<{
    select: [room: Room];
    toggle: [device: RoomDeviceCard];
}>();
</script>

<template>
    <article
        class="room-card"
        :class="{ selected }"
        @click="$emit('select', room)"
    >
        <header>
            <span class="room-avatar">{{ room.name.slice(0, 1) }}</span>
            <div>
                <h2>
                    {{ room.name }}
                    <small>{{ room.comfort >= 84 ? "舒适" : "良好" }}</small>
                </h2>
                <p><b></b>{{ room.onlineCount }} 个设备在线</p>
            </div>
        </header>
        <div class="room-metrics">
            <span><SvgIcon name="temperature" size="sm" />{{ room.temperature }}°C</span>
            <span><SvgIcon name="humidity" size="sm" />{{ room.humidity }}%</span>
            <span class="quality"><SvgIcon name="air-quality" size="sm" />优 {{ room.pm25 }}</span>
        </div>
        <div class="room-devices">
            <button
                v-for="device in devices.slice(0, 4)"
                :key="device.name"
                :class="{ on: room.deviceStates[device.key] }"
                type="button"
                @click.stop="$emit('select', room); $emit('toggle', device)"
            >
                <i><SvgIcon :name="device.icon" size="sm" /></i>
                <span>{{ device.name }}</span>
                <small>{{ room.deviceStates[device.key] ? "开" : "关" }}</small>
            </button>
        </div>
    </article>
</template>

<style scoped>
.room-card {
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px;
    box-shadow: var(--shadow-card);
    cursor: pointer;
    transition: 160ms var(--motion-ease);
}
.room-card:hover,
.room-card.selected {
    border-color: var(--color-primary-300);
    box-shadow: var(--shadow-card-hover);
}
.room-card > header {
    display: flex;
    align-items: center;
    gap: 10px;
}
.room-avatar {
    display: grid;
    width: 42px;
    height: 42px;
    place-items: center;
    border-radius: 11px;
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-700);
    font-weight: 900;
}
.room-card h2 {
    margin: 0;
    font-size: 15px;
}
.room-card h2 small {
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 2px 6px;
    color: var(--color-success);
    font-size: 9px;
}
.room-card header p {
    margin: 4px 0 0;
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.room-card header p b {
    display: inline-block;
    width: 6px;
    height: 6px;
    margin-right: 4px;
    border-radius: 50%;
    background: var(--color-success);
}
.room-metrics {
    display: flex;
    gap: 8px;
    margin: 12px 0;
}
.room-metrics span {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    border-radius: 7px;
    background: var(--color-surface-subtle);
    padding: 5px 7px;
    color: var(--color-text-secondary);
    font-size: 10px;
    font-weight: 800;
}
.room-metrics .quality {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.room-devices {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 6px;
}
.room-devices button {
    display: grid;
    min-width: 0;
    place-items: center;
    gap: 3px;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 7px 3px;
    color: var(--color-text-tertiary);
    font-size: 9px;
}
.room-devices button.on {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.room-devices i {
    font-style: normal;
}
.room-devices span {
    overflow: hidden;
    max-width: 100%;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 800;
}
.room-devices small {
    font-size: 8px;
}
</style>
