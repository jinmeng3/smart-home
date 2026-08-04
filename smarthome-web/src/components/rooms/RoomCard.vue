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
            <div class="room-title">
                <h2>{{ room.name }}</h2>
                <p class="room-status">
                    <small>{{ room.comfort >= 84 ? "舒适" : "良好" }}</small>
                    <b></b>{{ room.onlineCount }} 个设备在线
                </p>
            </div>
            <div class="room-metrics">
                <span><SvgIcon name="temperature" size="sm" />{{ room.temperature }}°C</span>
                <span><SvgIcon name="humidity" size="sm" />{{ room.humidity }}%</span>
                <span class="quality"><SvgIcon name="air-quality" size="sm" />优 {{ room.pm25 }}</span>
            </div>
        </header>
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
    gap: 8px;
}
.room-title {
    min-width: 0;
    flex: 1;
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
    overflow: hidden;
    margin: 0;
    font-size: 15px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.room-status {
    display: flex;
    align-items: center;
    gap: 5px;
    margin: 4px 0 0;
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.room-status small {
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 1px 6px;
    color: var(--color-success);
    font-size: 9px;
    line-height: 1.4;
}
.room-status b {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-success);
}
.room-metrics {
    display: flex;
    flex-shrink: 0;
    gap: 4px;
    margin: 0 0 0 auto;
}
.room-metrics span {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    border-radius: 6px;
    background: var(--color-surface-subtle);
    padding: 4px 6px;
    color: var(--color-text-secondary);
    font-size: 9px;
    font-weight: 800;
    white-space: nowrap;
}
.room-metrics .quality {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.room-devices {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 6px;
    margin-top: 10px;
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
