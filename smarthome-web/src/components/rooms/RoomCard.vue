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
            <span
                class="room-avatar"
                :class="room.roomType ? `is-${room.roomType}` : ''"
                >{{ room.name.slice(0, 1) }}</span
            >
            <div class="room-title">
                <h2>{{ room.name }}</h2>
                <p class="room-status">
                    <small>{{ room.comfort >= 84 ? "舒适" : "良好" }}</small>
                    <b></b>{{ room.onlineCount }} 个设备在线
                </p>
            </div>
        </header>
        <div class="room-metrics">
            <span><SvgIcon name="temperature" size="sm" />{{ room.temperature }}°C</span>
            <span><SvgIcon name="humidity" size="sm" />{{ room.humidity }}%</span>
            <span class="quality"><SvgIcon name="air-quality" size="sm" />优 {{ room.pm25 }}</span>
        </div>
        <div class="room-devices">
            <button
                v-for="device in devices"
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
    position: relative;
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 16px;
    box-shadow: var(--shadow-card);
    cursor: pointer;
    transition: 160ms var(--motion-ease);
}
.room-card:hover,
.room-card.selected {
    border-color: var(--color-primary-300);
    box-shadow: var(--shadow-card-hover);
}
.room-card.selected::before {
    position: absolute;
    top: 18px;
    bottom: 18px;
    left: -1px;
    width: 3px;
    border-radius: 0 999px 999px 0;
    background: var(--color-primary-600);
    content: "";
}
.room-card > header {
    display: flex;
    align-items: center;
    gap: 10px;
}
.room-title {
    min-width: 0;
    flex: 1;
}
.room-avatar {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 auto;
    place-items: center;
    border-radius: 11px;
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-700);
    font-weight: 900;
}

.room-avatar.is-living {
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-700);
}
.room-avatar.is-bedroom {
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--tone-indigo) 12%, var(--color-panel-background)),
        var(--tone-indigo-soft)
    );
    color: var(--color-scene-sleep);
}
.room-avatar.is-study {
    background: linear-gradient(135deg, var(--color-teal-soft), #f0fdfa);
    color: var(--color-teal-600);
}
.room-avatar.is-kitchen {
    background: linear-gradient(135deg, var(--color-warning-soft), #fffbeb);
    color: var(--color-device-light);
}
.room-avatar.is-bathroom {
    background: linear-gradient(135deg, var(--color-info-soft), #f0f9ff);
    color: var(--color-info);
}
.room-avatar.is-balcony {
    background: linear-gradient(135deg, var(--color-success-soft), #f0fdf4);
    color: var(--color-device-air);
}
.room-avatar.is-else {
    background: linear-gradient(
        135deg,
        var(--color-device-camera-soft),
        color-mix(in srgb, var(--color-device-camera-soft) 55%, var(--color-panel-background))
    );
    color: var(--color-device-camera);
}
.room-card h2 {
    overflow: hidden;
    margin: 0;
    font-size: 16px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.room-status {
    display: flex;
    align-items: center;
    gap: 5px;
    margin: 4px 0 0;
    color: var(--color-text-tertiary);
    font-size: 11px;
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
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 7px;
    margin-top: 14px;
}
.room-metrics span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    min-height: 34px;
    border-radius: 9px;
    background: var(--color-surface-subtle);
    padding: 5px 7px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
    white-space: nowrap;
}
.room-metrics .quality {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.room-devices {
    display: flex;
    gap: 7px;
    margin-top: 8px;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
}
.room-devices::-webkit-scrollbar {
    height: 3px;
}
.room-devices::-webkit-scrollbar-track {
    border-radius: 2px;
    background: var(--color-surface-subtle);
}
.room-devices::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border-strong);
}
.room-devices button {
    display: grid;
    min-width: 82px;
    flex: 0 0 auto;
    place-items: center;
    gap: 4px;
    min-height: 68px;
    border: 1px solid transparent;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    padding: 8px 10px;
    color: var(--color-text-tertiary);
    font-size: 10px;
    scroll-snap-align: start;
    transition: 160ms var(--motion-ease);
}
.room-devices button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-surface-hover);
}
.room-devices button.on {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.room-devices i {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-card-bg);
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
    color: var(--color-text-muted);
    font-size: 9px;
}
.room-devices button.on small {
    color: var(--color-primary-600);
}

@media (max-width: 620px) {
    .room-card {
        padding: 14px;
    }

    .room-devices button {
        min-width: 72px;
        padding: 6px 8px;
    }
}
</style>
