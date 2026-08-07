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
    delete: [room: Room];
}>();

const roomTypeIconMap: Record<string, string> = {
    living: "home",
    bedroom: "room",
    study: "comfort",
    kitchen: "plug",
    balcony: "illumination",
    bathroom: "humidity",
};

const roomTypeIcon = (room: Room) =>
    roomTypeIconMap[room.roomType] ?? "room";
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
            >
                <SvgIcon :name="roomTypeIcon(room)" size="sm" />
            </span>
            <div class="room-title">
                <h2>{{ room.name }}</h2>
                <p class="room-status">
                    <small>{{ room.comfort >= 84 ? "舒适" : "良好" }}</small>
                    <b></b>{{ room.onlineCount }}/{{ room.deviceCount }} 在线
                </p>
            </div>
            <button
                class="room-menu-btn"
                type="button"
                title="更多操作"
                @click.stop="$emit('delete', room)"
            >
                <SvgIcon name="more" size="sm" />
            </button>
        </header>
        <p class="room-meta">
            <SvgIcon name="home" size="sm" />{{ room.floor }}
            <span class="meta-sep"></span>
            <SvgIcon name="online-device" size="sm" />{{ room.onlineCount }} 个设备在线
        </p>
        <div class="room-devices">
            <button
                v-for="device in devices.slice(0, 3)"
                :key="device.id"
                :class="{ on: device.status === 'online' || device.status === 'running' }"
                type="button"
                @click.stop="$emit('select', room); $emit('toggle', device)"
            >
                <span class="device-icon-row">
                    <i :style="{ '--device-color': device.color || '#6b7280' }"><SvgIcon :name="device.icon" size="sm" /></i>
                    <span class="device-info">
                        <span class="device-name">{{ device.name }}</span>
                        <small class="device-status" :class="{ on: device.status === 'online' || device.status === 'running' }">{{ device.status === 'online' || device.status === 'running' ? "开" : "关" }}</small>
                    </span>
                </span>
            </button>
        </div>
    </article>
</template>

<style scoped>
.room-card {
    position: relative;
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 12px;
    box-shadow: var(--shadow-card);
    cursor: pointer;
    transition: 160ms var(--motion-ease);
    animation: room-card-enter 300ms var(--motion-ease) both;
}

@keyframes room-card-enter {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
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
    gap: 8px;
}
.room-title {
    min-width: 0;
    flex: 1;
}
.room-avatar {
    display: grid;
    width: 40px;
    height: 40px;
    flex: 0 0 auto;
    place-items: center;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-700);
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-primary-500) 14%, transparent);
}
.room-avatar :deep(svg),
.room-avatar svg {
    width: 20px;
    height: 20px;
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

.room-menu-btn {
    position: absolute;
    top: 6px;
    right: 6px;
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--color-text-muted);
    cursor: pointer;
    opacity: 0;
    transition: 160ms var(--motion-ease);
}
.room-card:hover .room-menu-btn,
.room-card.selected .room-menu-btn {
    opacity: 1;
}
.room-menu-btn:hover {
    background: var(--color-danger-soft);
    color: var(--color-danger);
    transform: scale(1.1);
}
.room-status {
    display: flex;
    align-items: center;
    gap: 4px;
    margin: 2px 0 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.room-status small {
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 0 5px;
    color: var(--color-success);
    font-size: 11px;
    line-height: 1.5;
}
.room-status b {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-success);
}
.room-meta {
    display: flex;
    align-items: center;
    gap: 4px;
    margin: 6px 0 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}
.room-meta svg {
    color: var(--color-text-muted);
}
.meta-sep {
    display: inline-block;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--color-border);
    margin: 0 4px;
}
.room-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
    margin-top: 10px;
}
.room-metrics span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    min-height: 28px;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 4px 6px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
}
.room-metrics .quality {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.room-devices {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
    margin-top: 6px;
}

.room-devices button {
    display: flex;
    align-items: center;
    gap: 6px;
    min-height: 48px;
    border: 1px solid transparent;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 6px 10px;
    color: var(--color-text-tertiary);
    font-size: 11px;
    transition: 160ms var(--motion-ease);
    cursor: pointer;
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
.room-devices .device-icon-row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1;
}
.room-devices i {
    display: grid;
    width: 28px;
    height: 28px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 7px;
    background: color-mix(in srgb, var(--device-color, #6b7280) 14%, transparent);
    color: var(--device-color, #6b7280);
    font-style: normal;
}
.room-devices .device-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
    flex: 1;
}
.room-devices .device-name {
    overflow: hidden;
    max-width: 100%;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 800;
    font-size: 12px;
    color: var(--color-text-primary);
    line-height: 1.2;
}
.room-devices .device-status {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-text-muted);
    line-height: 1.2;
}
.room-devices .device-status.on {
    color: var(--color-primary-600);
}
.room-devices button.on .device-name {
    color: var(--color-primary-700);
}
.room-devices button.on .device-status {
    color: var(--color-primary-500);
}
.room-devices small {
    color: var(--color-text-muted);
    font-size: 11px;
}
.room-devices button.on small {
    color: var(--color-primary-600);
}

@media (max-width: 620px) {
    .room-card {
        padding: 14px;
    }

    .room-devices {
        gap: 4px;
    }
    .room-devices button {
        padding: 4px 6px;
        min-height: 48px;
    }
}
</style>
