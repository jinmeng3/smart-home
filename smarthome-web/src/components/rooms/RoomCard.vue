<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Room, RoomDeviceCard } from "../../types/room";
import { getRoomTypeIcon } from "./roomMeta";

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

const roomTypeIcon = (room: Room) =>
    getRoomTypeIcon(room.roomType);
</script>

<template>
    <article
        class="room-card"
        :class="{ selected }"
        :style="{ '--theme-color': room.themeColor || '#3478f6' }"
        role="button"
        tabindex="0"
        @click="$emit('select', room)"
        @keydown.enter="$emit('select', room)"
        @keydown.space.prevent="$emit('select', room)"
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
                    <span class="online-indicator">
                        <i></i>
                        {{ room.onlineCount }}/{{ room.deviceCount }} 在线
                    </span>
                    <span class="comfort-badge">舒适度 {{ room.comfort }}</span>
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
    padding: 16px;
    box-shadow: var(--shadow-card);
    cursor: pointer;
    transition: 220ms var(--motion-ease);
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

.room-card:hover {
    border-color: var(--color-border-strong);
}

.room-card:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
}

.room-card.selected {
    border-color: color-mix(in srgb, var(--theme-color, #3478f6) 50%, var(--color-border));
    background: color-mix(in srgb, var(--theme-color, #3478f6) 5%, transparent);
}

/* 选中态左侧色条 */
.room-card.selected::before {
    position: absolute;
    top: 12px;
    bottom: 12px;
    left: -1px;
    width: 3px;
    border-radius: 0 999px 999px 0;
    background: var(--theme-color, #3478f6);
    content: "";
}

.room-card > header {
    display: flex;
    align-items: center;
    gap: 12px;
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
    font-size: 17px;
    font-weight: 700;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.room-status {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 6px 0 0;
}

.online-indicator {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.online-indicator i {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-success);
}

.comfort-badge {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 1px 7px;
    color: var(--color-success);
    font-size: 11px;
    font-weight: 800;
    line-height: 1.5;
}

.room-menu-btn {
    display: grid;
    width: 32px;
    height: 32px;
    flex: 0 0 32px;
    place-items: center;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--color-text-muted);
    cursor: pointer;
    opacity: 0;
    transition: 120ms var(--motion-ease);
}

.room-card:hover .room-menu-btn,
.room-card.selected .room-menu-btn,
.room-menu-btn:focus-visible {
    opacity: 1;
}

.room-menu-btn:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-secondary);
}

.room-devices {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
    margin-top: 10px;
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

.room-devices button:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 1px;
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

@media (prefers-reduced-motion: reduce) {
    .room-card,
    .room-menu-btn {
        transition-duration: 1ms;
    }
    .room-card:hover {
        transform: none;
    }
    .room-menu-btn:hover {
        transform: none;
    }
}
</style>