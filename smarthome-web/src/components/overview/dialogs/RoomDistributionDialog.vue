<script setup lang="ts">
import { computed } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";

interface RoomData {
    name: string;
    icon: string;
    count: number;
    light: string;
    air: string;
    extra: string;
    tone: string;
}

const props = defineProps<{
    modelValue: boolean;
    rooms: RoomData[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

// Map room names to more specific icons
const roomIconMap: Record<string, string> = {
    "客厅": "home",
    "主卧": "room",
    "次卧": "room",
    "厨房": "plug",
    "卫生间": "humidity",
    "阳台": "illumination",
};

const getRoomIcon = (room: RoomData) => roomIconMap[room.name] || room.icon;

const totalDevices = computed(() =>
    props.rooms.reduce((sum, room) => sum + room.count, 0),
);

const activeRooms = computed(() =>
    props.rooms.filter((r) => r.count > 0).length,
);

const avgDevices = computed(() =>
    props.rooms.length ? (totalDevices.value / props.rooms.length).toFixed(1) : "0",
);

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="房间分布"
        description="查看全屋房间布局与设备分布情况"
        width="740px"
        closable
        :close-on-overlay="true"
        @update:model-value="close"
    >
        <div class="distribution-layout">
            <!-- Summary Stats Bar -->
            <header class="distribution-summary">
                <div class="summary-stat">
                    <span class="summary-icon is-room">
                        <SvgIcon name="room" size="sm" />
                    </span>
                    <div class="summary-body">
                        <b>{{ rooms.length }}</b>
                        <small>个房间</small>
                    </div>
                </div>
                <div class="summary-stat">
                    <span class="summary-icon is-device">
                        <SvgIcon name="online-device" size="sm" />
                    </span>
                    <div class="summary-body">
                        <b>{{ totalDevices }}</b>
                        <small>台设备</small>
                    </div>
                </div>
                <div class="summary-stat">
                    <span class="summary-icon is-active">
                        <SvgIcon name="check-circle" size="sm" />
                    </span>
                    <div class="summary-body">
                        <b>{{ activeRooms }}</b>
                        <small>已启用</small>
                    </div>
                </div>
                <div class="summary-stat">
                    <span class="summary-icon is-average">
                        <SvgIcon name="grid" size="sm" />
                    </span>
                    <div class="summary-body">
                        <b>{{ avgDevices }}</b>
                        <small>平均/间</small>
                    </div>
                </div>
            </header>

            <!-- Room Grid -->
            <div class="room-grid">
                <article
                    v-for="(room, index) in rooms"
                    :key="room.name"
                    class="room-card"
                    :style="{ '--i': index }"
                >
                    <!-- Card Header -->
                    <div class="room-card-header">
                        <i :class="room.tone">
                            <SvgIcon :name="getRoomIcon(room)" size="lg" />
                        </i>
                        <div class="room-card-title">
                            <strong>{{ room.name }}</strong>
                            <span class="device-badge">{{ room.count }} 个设备</span>
                        </div>
                        <!-- Status dot -->
                        <span
                            class="status-dot"
                            :class="room.count > 0 ? 'is-online' : 'is-offline'"
                            :title="room.count > 0 ? '设备在线' : '暂无设备'"
                        />
                    </div>

                    <!-- Card Body -->
                    <div class="room-card-body">
                        <div class="room-detail-row">
                            <span class="detail-label">
                                <SvgIcon name="light" size="sm" /> 灯光
                            </span>
                            <span class="detail-value">{{ room.light }}</span>
                        </div>
                        <div class="room-detail-row">
                            <span class="detail-label">
                                <SvgIcon name="air-conditioner" size="sm" /> 设备
                            </span>
                            <span class="detail-value">{{ room.air }}</span>
                        </div>
                        <div class="room-detail-row">
                            <span class="detail-label">
                                <SvgIcon name="sensor" size="sm" /> 状态
                            </span>
                            <span class="detail-value">{{ room.extra }}</span>
                        </div>
                    </div>

                    <!-- Mini utilization bar -->
                    <div class="room-util-bar">
                        <span
                            class="util-fill"
                            :class="room.tone"
                            :style="{ width: Math.min((room.count / 8) * 100, 100) + '%' }"
                        />
                    </div>
                </article>
            </div>
        </div>

        <template #footer></template>
    </BaseSmartModal>
</template>

<style scoped>
.distribution-layout {
    display: grid;
    gap: 20px;
    padding: 4px 0;
}

/* ── Summary Stats Bar ── */
.distribution-summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    padding: 16px 20px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        var(--color-surface-subtle) 0%,
        var(--color-card-bg) 100%
    );
}

.summary-stat {
    display: flex;
    align-items: center;
    gap: 10px;
}

.summary-stat + .summary-stat {
    padding-left: 10px;
    border-left: 1px solid var(--color-border);
}

.summary-icon {
    display: grid;
    width: 40px;
    height: 40px;
    flex: none;
    place-items: center;
    border-radius: 10px;
    transition: transform 200ms var(--motion-ease);
}

.summary-stat:hover .summary-icon {
    transform: scale(1.08);
}

.summary-icon.is-room {
    background: linear-gradient(135deg, #e9f2ff, #d6e5ff);
    color: #2871f5;
}

.summary-icon.is-device {
    background: linear-gradient(135deg, #e7f9ee, #d0f3de);
    color: #20b86a;
}

.summary-icon.is-active {
    background: linear-gradient(135deg, #fff3e0, #ffe8c8);
    color: #f07821;
}

.summary-icon.is-average {
    background: linear-gradient(135deg, #eee9ff, #e0d8ff);
    color: #7651ee;
}

.summary-body {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
}

.summary-body b {
    font-size: 20px;
    font-weight: 900;
    line-height: 1.1;
    color: var(--color-text-primary);
}

.summary-body small {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    white-space: nowrap;
}

/* ── Room Grid ── */
.room-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.room-card {
    position: relative;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 16px;
    animation: card-enter 360ms var(--motion-ease) both;
    animation-delay: calc(var(--i, 0) * 60ms);
    transition:
        border-color 200ms var(--motion-ease),
        box-shadow 200ms var(--motion-ease),
        transform 200ms var(--motion-ease);
}

.room-card:hover {
    border-color: var(--color-border-default);
    box-shadow:
        0 4px 16px rgba(0, 0, 0, 0.06),
        0 1px 4px rgba(0, 0, 0, 0.04);
    transform: translateY(-2px);
}

@keyframes card-enter {
    from {
        opacity: 0;
        transform: translateY(12px) scale(0.97);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* ── Card Header ── */
.room-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border-subtle);
}

.room-card-header i {
    display: grid;
    width: 42px;
    height: 42px;
    flex: none;
    place-items: center;
    border-radius: 12px;
    transition: transform 200ms var(--motion-ease);
}

.room-card:hover .room-card-header i {
    transform: scale(1.05);
}

.room-card-header i.blue {
    background: linear-gradient(135deg, var(--color-info-soft, #e9f2ff), #d6e5ff);
    color: var(--color-info, #2871f5);
}

.room-card-header i.orange {
    background: linear-gradient(135deg, var(--color-warning-soft, #fff3e0), #ffe8c8);
    color: var(--color-warning, #f07821);
}

.room-card-header i.green {
    background: linear-gradient(135deg, var(--color-success-soft, #e7f9ee), #d0f3de);
    color: var(--color-success, #20b86a);
}

.room-card-header i.purple {
    background: linear-gradient(135deg, #eee9ff, #e0d8ff);
    color: #7651ee;
}

.room-card-title {
    flex: 1;
    min-width: 0;
}

.room-card-title strong {
    display: block;
    overflow: hidden;
    font-size: 14px;
    font-weight: 900;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-badge {
    display: inline-block;
    margin-top: 2px;
    padding: 1px 8px;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    font-size: 10px;
    font-weight: 800;
    color: var(--color-text-tertiary);
    white-space: nowrap;
}

.status-dot {
    width: 8px;
    height: 8px;
    flex: none;
    border-radius: 50%;
    transition: background 200ms var(--motion-ease);
}

.status-dot.is-online {
    background: #20b86a;
    box-shadow: 0 0 0 2px rgba(32, 184, 106, 0.2);
}

.status-dot.is-offline {
    background: #c0c9d6;
}

/* ── Card Body ── */
.room-card-body {
    display: grid;
    gap: 6px;
    padding-top: 10px;
    flex: 1;
}

.room-detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    padding: 3px 0;
}

.detail-label {
    display: flex;
    align-items: center;
    gap: 5px;
    color: var(--color-text-tertiary);
    font-weight: 700;
}

.detail-label :deep(.orion-icon) {
    opacity: 0.6;
}

.detail-value {
    color: var(--color-text-secondary);
    font-weight: 800;
    text-align: right;
    font-size: 12px;
}

/* ── Utilization Bar ── */
.room-util-bar {
    height: 3px;
    margin-top: 12px;
    border-radius: 4px;
    background: var(--color-surface-subtle);
    overflow: hidden;
}

.util-fill {
    display: block;
    height: 100%;
    border-radius: 4px;
    transition: width 600ms var(--motion-ease);
}

.util-fill.blue {
    background: linear-gradient(90deg, #2871f5, #5b93f7);
}

.util-fill.orange {
    background: linear-gradient(90deg, #f07821, #f59a4d);
}

.util-fill.green {
    background: linear-gradient(90deg, #20b86a, #4cd48a);
}

.util-fill.purple {
    background: linear-gradient(90deg, #7651ee, #9e7ef5);
}

.util-fill.teal {
    background: linear-gradient(90deg, #0d9488, #14b8a6);
}

/* ── Responsive ── */
@media (max-width: 640px) {
    .distribution-summary {
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        padding: 14px;
    }

    .summary-stat:nth-child(n + 3) {
        border-left: none;
        padding-left: 0;
    }

    .summary-stat:nth-child(odd) + .summary-stat:nth-child(even) {
        border-left: 1px solid var(--color-border);
        padding-left: 10px;
    }

    .room-grid {
        grid-template-columns: 1fr;
        gap: 10px;
    }

    .room-card {
        padding: 14px;
    }
}
</style>