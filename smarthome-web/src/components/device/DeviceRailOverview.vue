<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import DeviceRailActions, { type RailAction } from "./DeviceRailActions.vue";

defineProps<{
    stats: {
        online: number;
        offline: number;
        warning: number;
        monthlyNew: number;
    };
    total: number;
}>();

const emit = defineEmits<{
    action: [key: string];
    sync: [];
}>();

/** 未选择设备时的全局快捷操作 */
const globalActions: RailAction[] = [
    { key: "sync", label: "同步设备", tone: "primary", icon: "refresh" },
    { key: "scan", label: "设备巡检", tone: "success", icon: "scan" },
    { key: "delete", label: "批量管理", tone: "danger", icon: "delete" },
    { key: "logs", label: "查看日志", tone: "warning", icon: "log" },
];

const handleAction = (key: string) => {
    if (key === "sync") {
        emit("sync");
        return;
    }
    emit("action", key);
};
</script>

<template>
    <div class="rail-overview">
        <!-- 设备统计 -->
        <section class="rail-stats">
            <div class="rail-stat">
                <span class="rail-stat-icon is-success">
                    <SvgIcon name="online-device" size="sm" />
                </span>
                <strong>{{ stats.online }}</strong>
                <small>在线</small>
            </div>
            <div class="rail-stat">
                <span class="rail-stat-icon is-muted">
                    <SvgIcon name="offline-device" size="sm" />
                </span>
                <strong>{{ stats.offline }}</strong>
                <small>离线</small>
            </div>
            <div class="rail-stat">
                <span class="rail-stat-icon is-warning">
                    <SvgIcon name="warning" size="sm" />
                </span>
                <strong>{{ stats.warning }}</strong>
                <small>告警</small>
            </div>
        </section>

        <p class="rail-overview-hint">
            当前共 {{ total }} 台设备，选择设备后查看详情
        </p>

        <DeviceRailActions :actions="globalActions" @action="handleAction" />
    </div>
</template>

<style scoped>
.rail-overview {
    display: grid;
    gap: 12px;
    padding: 14px 14px 0;
}

.rail-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    padding: 13px;
    background: var(--color-panel-background);
    box-shadow: var(--shadow-card);
}

.rail-stat {
    display: grid;
    gap: 2px;
    justify-items: center;
    padding: 8px 4px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--color-panel-secondary);
}

.rail-stat-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-surface-subtle);
}

.rail-stat-icon.is-success { color: var(--color-success); }
.rail-stat-icon.is-warning { color: var(--color-warning); }
.rail-stat-icon.is-muted { color: var(--color-text-muted); }

.rail-stat strong {
    font-size: 18px;
    font-weight: 900;
    color: var(--color-text-primary);
    line-height: 1.1;
}

.rail-stat small {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}

.rail-overview-hint {
    margin: -3px 2px 0;
    font-size: 11px;
    color: var(--color-text-muted);
}
</style>
