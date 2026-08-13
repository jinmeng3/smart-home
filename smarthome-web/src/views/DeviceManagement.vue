<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import BaseCollapsibleRail from "../components/common/BaseCollapsibleRail.vue";
import BaseSmartModal from "../components/common/BaseSmartModal.vue";
import ConfirmActionDialog from "../components/common/ConfirmActionDialog.vue";
import ConfirmEntitySummary from "../components/common/ConfirmEntitySummary.vue";
import PageHeader from "../components/common/PageHeader.vue";
import RailIndicator from "../components/common/RailIndicator.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import DeviceList from "../components/device/DeviceList.vue";
import DeviceRailDetail from "../components/device/DeviceRailDetail.vue";
import DeviceRailOverview from "../components/device/DeviceRailOverview.vue";
import DeviceStatsCard from "../components/device/DeviceStatsCard.vue";
import DeviceToolbar from "../components/device/DeviceToolbar.vue";
import PlatformAccessList from "../components/device/PlatformAccessList.vue";
import {
    deviceStatusLabelMap,
    getDeviceTypeIcon,
} from "../components/device/deviceMeta";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { useDeviceManagementController } from "../composables/useDeviceManagementController";
import type { DeviceQuickActionKey } from "../composables/useDeviceManagementController";
import { defineAsyncDialog } from "../utils/asyncDialog";

const DeviceEditorDialog = defineAsyncDialog(
    () => import("../components/device/DeviceEditorDialog.vue"),
);
const SyncDialog = defineAsyncDialog(
    () => import("../components/device/SyncDialog.vue"),
);

const controller = useDeviceManagementController();
const route = useRoute();

/* ── 页面显式解构 refs，模板不再出现 controller.x.value ── */
const {
    batchDeleteDialogOpen,
    batchDeleting,
    batchDeletingIds,
    batchDeletingDevices,
    batchMode,
    connectedCount,
    deleteDialogOpen,
    deleting,
    deletingDevice,
    deviceLogs,
    editingDevice,
    editorOpen,
    filters,
    loading,
    logActionLabel,
    logDeviceName,
    logDialogOpen,
    platforms,
    rooms,
    saving,
    selectedDevice,
    selectedDeviceIds,
    selectedId,
    sort,
    sortedDevices,
    stats,
    syncing,
    total,
} = controller;

const loadDevices = useAuthenticatedLoader(controller.loadDevices, {
    immediate: false,
});

onMounted(() => {
    // Read view parameter from URL
    const view = route.query.view as "all" | "frequent" | "favorite" | undefined;
    if (view === "frequent" || view === "favorite") {
        controller.setViewMode(view);
    }
    void loadDevices();
});

/** 清空全部筛选条件（搜索词/类型/状态/房间），防抖 watch 会自动重新加载 */
const clearDeviceFilters = () => {
    for (const key of ["keyword", "type", "status", "room"] as const) {
        if (filters[key] !== "") {
            controller.updateFilter(key, "");
        }
    }
};

/* ── 侧栏折叠状态（由 BaseCollapsibleRail 维护，v-model 同步） ── */
const railCollapsed = ref(false);
const syncDialogOpen = ref(false);

/* ── 同步弹窗处理 ──────────────────────────────────────────────── */
const handleSync = () => {
    syncDialogOpen.value = true;
};

const handlePlatformSync = async (_platformName: string) => {
    return await controller.runSync();
};

/* ── 侧栏快捷操作分发 ──────────────────────────────────────────── */
const handleRailAction = (key: string) => {
    if (key === "sync") {
        handleSync();
        return;
    }

    if (key === "edit") {
        if (selectedDevice.value) {
            controller.editDevice(selectedDevice.value);
        }
        return;
    }

    controller.runQuickAction(key as DeviceQuickActionKey);
};

const handleRailSync = () => {
    handleSync();
};
</script>

<template>
    <div
        class="app-page-layout"
        :class="{ 'rail-collapsed-layout': railCollapsed }"
    >
        <section class="device-management-page page-shell page-enter">
            <PageHeader
                title="设备管理"
                description="家庭设备与接入管理"
                icon="device-management"
                tone="var(--color-device-light)"
                soft="var(--color-warning-soft)"
            >
                <DeviceToolbar
                    :keyword="filters.keyword"
                    :room="filters.room"
                    :rooms="rooms"
                    :status="filters.status"
                    @add="controller.addDevice"
                    @update:keyword="(value) => controller.updateFilter('keyword', value)"
                    @update:room="(value) => controller.updateFilter('room', value)"
                    @update:status="(value) => controller.updateFilter('status', value)"
                />
            </PageHeader>

            <div class="device-stats-grid">
                <DeviceStatsCard
                    icon="online-device"
                    label="在线设备"
                    :value="stats.online"
                    tone="success"
                    :delay="0"
                />
                <DeviceStatsCard
                    icon="offline-device"
                    label="离线设备"
                    :value="stats.offline"
                    tone="muted"
                    :delay="40"
                />
                <DeviceStatsCard
                    icon="warning"
                    label="告警设备"
                    :value="stats.warning"
                    tone="warning"
                    :delay="80"
                />
                <DeviceStatsCard
                    icon="new-device"
                    label="本月新增"
                    :value="stats.monthlyNew"
                    tone="primary"
                    :delay="120"
                />
            </div>

            <DeviceList
                :active-type="filters.type"
                :batch-mode="batchMode"
                :selected-device-ids="selectedDeviceIds"
                :devices="sortedDevices"
                :loading="loading"
                :page="filters.page"
                :page-size="filters.pageSize"
                :selected-id="selectedId"
                :sort="sort"
                :syncing="syncing"
                :total="total"
                @batch="
                    batchMode &&
                    selectedDeviceIds.length
                        ? controller.batchDeleteDevices(selectedDeviceIds)
                        : controller.toggleBatchMode()
                "
                @batch-select="controller.toggleSelectDevice"
                @edit="controller.editDevice"
                @remove="controller.removeDevice"
                @select="controller.selectDevice"
                @sync="handleSync"
                @update:active-type="(value) => controller.updateFilter('type', value)"
                @update:page="controller.updatePage"
                @update:page-size="controller.updatePageSize"
                @update:sort="sort = $event"
                @clear-filters="clearDeviceFilters"
            />
        </section>

        <BaseCollapsibleRail
            v-model:collapsed="railCollapsed"
            :title="selectedDevice ? '设备详情' : '设备概览'"
            :subtitle="
                selectedDevice
                    ? `${selectedDevice.name} · ${selectedDevice.room}`
                    : '家庭设备与平台连接状态'
            "
            storage-key="orion.device-context-rail-collapsed"
        >
            <template #collapsed>
                <RailIndicator
                    v-if="selectedDevice"
                    :icon="getDeviceTypeIcon(selectedDevice.icon || selectedDevice.type)"
                    :dot="selectedDevice.status"
                    :tooltip="`${selectedDevice.name} · ${deviceStatusLabelMap[selectedDevice.status]}`"
                />
                <RailIndicator
                    v-else
                    icon="online-device"
                    tone="success"
                    :tooltip="`${stats.online} 台设备在线`"
                />
                <RailIndicator
                    icon="platform"
                    :tone="connectedCount > 0 ? 'success' : 'muted'"
                    :tooltip="`${connectedCount}/${platforms.length} 个平台已连接`"
                />
                <RailIndicator
                    v-if="stats.warning > 0"
                    icon="warning"
                    tone="danger"
                    :badge="stats.warning"
                    :tooltip="`${stats.warning} 条告警`"
                />
            </template>

            <template #default>
                <Transition name="rail-mode" mode="out-in">
                    <DeviceRailDetail
                        v-if="selectedDevice"
                        :key="`detail-${selectedDevice.id}`"
                        :device="selectedDevice"
                        :syncing="syncing"
                        @action="handleRailAction"
                        @sync="handleRailSync"
                    />
                    <DeviceRailOverview
                        v-else
                        key="overview"
                        :stats="stats"
                        :total="total"
                        @action="handleRailAction"
                        @sync="handleRailSync"
                    />
                </Transition>

                <PlatformAccessList
                    :platforms="platforms"
                    :syncing="syncing"
                    @sync="handleRailSync"
                />
            </template>
        </BaseCollapsibleRail>

        <SyncDialog
            v-if="syncDialogOpen"
            v-model="syncDialogOpen"
            :platforms="platforms"
            :syncing="syncing"
            :sync-handler="handlePlatformSync"
        />

        <DeviceEditorDialog
            v-if="editorOpen"
            v-model="editorOpen"
            :device="editingDevice"
            :loading="saving"
            @submit="controller.saveDevice"
        />

        <ConfirmActionDialog
            v-if="deleteDialogOpen"
            :loading="deleting"
            :model-value="deleteDialogOpen"
            title="删除设备"
            description="此操作会从设备管理中移除该设备。"
            warning="删除后将无法在设备列表、智能对话设备清单和快捷操作中继续管理该设备。"
            footer-hint="确认后会立即调用后端删除接口。"
            @cancel="controller.cancelRemoveDevice"
            @confirm="controller.confirmRemoveDevice"
            @update:model-value="deleteDialogOpen = $event"
        >
            <section v-if="deletingDevice" class="delete-dialog-body">
                <ConfirmEntitySummary
                    :description="`${deletingDevice.room} · ${deletingDevice.brand}`"
                    icon="device-management"
                    :title="deletingDevice.name"
                />
            </section>
        </ConfirmActionDialog>

        <ConfirmActionDialog
            v-if="batchDeleteDialogOpen"
            :loading="batchDeleting"
            :model-value="batchDeleteDialogOpen"
            title="批量删除设备"
            description="请核对设备清单，确认后将立即移除。"
            warning="设备信息、关联日志和绑定关系将被永久删除，且无法撤销。"
            footer-hint="删除操作不可撤销"
            @cancel="controller.cancelBatchDelete"
            @confirm="controller.confirmBatchDelete"
            @update:model-value="batchDeleteDialogOpen = $event"
        >
            <section class="batch-delete-body">
                <div
                    v-if="batchDeleting"
                    class="batch-delete-progress"
                >
                    <div class="batch-delete-progress-bar">
                        <div class="batch-delete-progress-fill"></div>
                    </div>
                    <span class="batch-delete-progress-label">正在删除…</span>
                </div>

                <div v-if="!batchDeleting" class="batch-delete-summary">
                    <div class="batch-delete-summary-icon" aria-hidden="true">
                        <SvgIcon name="delete" />
                    </div>
                    <div class="batch-delete-summary-copy">
                        <div class="batch-delete-count">
                            <span class="batch-delete-number">{{ batchDeletingIds.length }}</span>
                            <span class="batch-delete-unit">台设备待删除</span>
                        </div>
                        <p class="batch-delete-hint">
                            请确认以下设备是否正确
                        </p>
                    </div>
                </div>

                <div v-if="!batchDeleting" class="batch-delete-list">
                    <div
                        v-for="device in batchDeletingDevices.slice(0, 6)"
                        :key="device.id"
                        class="batch-delete-item"
                    >
                        <span class="batch-delete-item-icon">
                            <SvgIcon name="device-management" size="sm" />
                        </span>
                        <span class="batch-delete-item-name">{{ device.name }}</span>
                        <span class="batch-delete-item-room">{{ device.room }}</span>
                    </div>
                    <div
                        v-if="batchDeletingIds.length > 6"
                        class="batch-delete-more"
                    >
                        还有 {{ batchDeletingIds.length - 6 }} 台设备
                    </div>
                </div>
            </section>
        </ConfirmActionDialog>

        <BaseSmartModal
            v-if="logDialogOpen"
            :model-value="logDialogOpen"
            width="640px"
            @update:model-value="!$event && controller.closeLogDialog()"
        >
            <template #header>
                <header class="log-dialog-header">
                    <span class="log-dialog-icon" aria-hidden="true">
                        <SvgIcon name="log" />
                    </span>
                    <div>
                        <h2>设备日志</h2>
                        <p class="log-dialog-subtitle">
                            {{ logDeviceName }}
                            <span class="log-count-badge">{{ deviceLogs.length }}</span>
                            条操作记录
                        </p>
                    </div>
                    <button
                        class="log-dialog-close"
                        type="button"
                        aria-label="关闭"
                        @click="controller.closeLogDialog"
                    >
                        <SvgIcon name="close" size="sm" />
                    </button>
                </header>
            </template>

            <section class="log-dialog-body">
                <div v-if="!deviceLogs.length" class="log-empty">
                    <SvgIcon name="log" size="lg" />
                    <span>该设备暂无操作日志</span>
                </div>

                <div class="log-timeline">
                    <div
                        v-for="(log, index) in deviceLogs"
                        :key="log.id"
                        class="log-item"
                        :style="{ '--i': index }"
                    >
                        <div class="log-timeline-node">
                            <span class="log-dot" :class="`is-${log.action}`"></span>
                            <div
                                v-if="index < deviceLogs.length - 1"
                                class="log-line"
                                :class="`is-${log.action}`"
                            ></div>
                        </div>
                        <div class="log-card" :class="`is-${log.action}`">
                            <div class="log-card-top">
                                <span class="log-action-label">{{ logActionLabel(log.action) }}</span>
                                <time class="log-time">{{ log.createdAt }}</time>
                            </div>
                            <p class="log-message">{{ log.message }}</p>
                        </div>
                    </div>
                </div>
            </section>
        </BaseSmartModal>
    </div>
</template>

<style scoped>
.device-management-page {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 12px;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 14px;
}

.batch-mode-bar {
    display: flex;
    align-items: center;
    margin-top: 12px;
}

.batch-mode-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    padding: 6px 14px;
    background: var(--color-surface);
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: all 160ms var(--motion-ease);
}

.batch-mode-toggle:hover {
    border-color: var(--color-primary-400);
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}

.batch-mode-toggle.is-active {
    border-color: var(--color-primary-500);
    color: #fff;
    background: var(--color-primary-600);
}

.batch-action-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid var(--color-primary-200);
    border-radius: 10px;
    padding: 10px 16px;
    margin-bottom: 16px;
    background: var(--color-primary-50);
    animation: batch-bar-enter 220ms var(--motion-ease) both;
}

.batch-action-count {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 600;
}

.batch-action-count strong {
    color: var(--color-primary-600);
    font-size: 15px;
}

.batch-action-tools {
    display: flex;
    gap: 8px;
}

.batch-action-clear {
    border: 1px solid var(--color-border-subtle);
    border-radius: 6px;
    padding: 5px 12px;
    background: var(--color-surface);
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 160ms var(--motion-ease);
}

.batch-action-clear:hover {
    border-color: var(--color-border);
    color: var(--color-text-primary);
}

.batch-action-delete {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border: 0;
    border-radius: 6px;
    padding: 5px 12px;
    background: var(--color-danger-600);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 160ms var(--motion-ease);
}

.batch-action-delete:hover {
    background: var(--color-danger-700);
    transform: translateY(-1px);
}

@keyframes batch-bar-enter {
    from {
        opacity: 0;
        transform: translateY(-8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.device-stats-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
}

/* ── 双栏布局（与 components.css 的 .app-page-layout 保持一致） ── */
/* 仅桌面端（≥1024px）为双栏；移动端保持单栏。 */
/* 使用 auto 列 + rail 自身 width 过渡实现平滑动画。 */
@media (min-width: 1024px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }

    .app-page-layout.rail-collapsed-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

@media (min-width: 1024px) and (max-width: 1279px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }

    .app-page-layout.rail-collapsed-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

@media (prefers-reduced-motion: reduce) {
    .app-page-layout {
        transition: none;
    }
}

/* ── 侧栏概览 ↔ 详情模式切换（out-in 交叉淡入） ── */
.rail-mode-enter-active,
.rail-mode-leave-active {
    transition:
        opacity 160ms ease,
        transform 180ms var(--motion-ease);
}

.rail-mode-enter-from {
    opacity: 0;
    transform: translateY(4px);
}

.rail-mode-leave-to {
    opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
    .rail-mode-enter-active,
    .rail-mode-leave-active {
        transition-duration: 1ms;
    }
}

.delete-dialog-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 22px;
    border-bottom: 1px solid var(--color-danger-border);
    background: linear-gradient(
        180deg,
        var(--color-card-bg),
        var(--color-danger-soft)
    );
}

.delete-dialog-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.delete-dialog-header h2,
.delete-dialog-header p {
    margin: 0;
}

.delete-dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 20px;
    font-weight: 900;
}

.delete-dialog-header p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
}

.delete-dialog-close {
    display: grid;
    width: 34px;
    height: 34px;
    margin-left: auto;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
}

.delete-dialog-close:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.delete-dialog-body {
    display: grid;
    gap: 14px;
}

.delete-device-summary {
    display: grid;
    grid-template-columns: 46px minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 14px;
}

.delete-device-thumb {
    display: grid;
    width: 46px;
    height: 46px;
    place-items: center;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-primary-700);
}

.delete-device-summary strong,
.delete-device-summary p {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.delete-device-summary strong {
    display: block;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
}

.delete-device-summary p,
.delete-dialog-warning,
.delete-dialog-footer span {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.delete-device-summary p {
    margin: 4px 0 0;
}

.delete-dialog-warning {
    margin: 0;
    border: 1px solid var(--color-danger-border);
    border-radius: 10px;
    background: var(--color-danger-soft);
    padding: 12px 14px;
    color: var(--color-danger);
    line-height: 1.6;
}

.delete-dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 14px 22px;
    border-top: 1px solid var(--color-border-subtle);
    background: var(--color-workspace-background);
}

.delete-dialog-footer div {
    display: flex;
    flex-shrink: 0;
    gap: 10px;
}

.delete-cancel-button,
.delete-confirm-button {
    display: inline-flex;
    height: 38px;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border-radius: 9px;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 900;
}

.delete-cancel-button {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.delete-confirm-button {
    border: 1px solid var(--color-danger);
    background: var(--color-danger);
    color: var(--color-text-on-primary);
    box-shadow: 0 6px 16px var(--color-danger-soft);
}

.delete-confirm-button:disabled svg {
    animation: delete-dialog-spin 900ms linear infinite;
}

button:disabled {
    cursor: default;
    opacity: 0.55;
}

@keyframes delete-dialog-spin {
    to {
        transform: rotate(360deg);
    }
}

@media (max-width: 1180px) {
    .device-stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

}

@media (max-width: 480px) {
    .device-management-page {
        padding: 12px;
    }
    .device-stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 360px) {
    .device-stats-grid {
        grid-template-columns: 1fr;
    }
}

@media (prefers-reduced-motion: reduce) {
    .device-management-page {
        animation: none;
    }
    .device-stats-card,
    .device-list-panel,
    .log-item,
    .batch-action-bar {
        animation: none !important;
        transition-duration: 1ms !important;
    }
}

/* ── 批量删除弹窗 ───────────────────────────────────────────────────── */

.batch-delete-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 22px;
    border-bottom: 1px solid var(--color-danger-border);
    background: linear-gradient(
        180deg,
        var(--color-card-bg),
        var(--color-danger-soft)
    );
}

.batch-delete-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.batch-delete-header h2,
.batch-delete-header p {
    margin: 0;
}

.batch-delete-header h2 {
    color: var(--color-text-primary);
    font-size: 20px;
    font-weight: 900;
}

.batch-delete-header p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
}

.batch-delete-close {
    display: grid;
    width: 34px;
    height: 34px;
    margin-left: auto;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
}

.batch-delete-close:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.batch-delete-body {
    display: grid;
    gap: 12px;
    padding: 0;
}

.batch-delete-summary {
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    border: 1px solid var(--color-danger-border);
    border-radius: 12px;
    margin: 0;
    padding: 12px 14px;
    background: color-mix(in srgb, var(--color-danger-soft) 68%, var(--color-card-bg));
}

.batch-delete-summary-icon {
    display: grid;
    width: 42px;
    height: 42px;
    place-items: center;
    border-radius: 11px;
    background: var(--color-card-bg);
    color: var(--color-danger);
    box-shadow: 0 4px 12px color-mix(in srgb, var(--color-danger) 12%, transparent);
}

.batch-delete-summary-copy {
    display: grid;
    min-width: 0;
    gap: 3px;
}

.batch-delete-count {
    display: flex;
    align-items: baseline;
    gap: 6px;
}

.batch-delete-number {
    font-size: 26px;
    font-weight: 900;
    color: var(--color-danger);
    line-height: 1;
}

.batch-delete-unit {
    font-size: 14px;
    font-weight: 900;
    color: var(--color-text-secondary);
}

.batch-delete-hint {
    margin: 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
    line-height: 1.45;
}

.batch-delete-list {
    display: grid;
    gap: 2px;
    max-height: 248px;
    margin: 0;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    overflow: hidden;
    overflow-y: auto;
    scrollbar-color: var(--color-border-strong) transparent;
    scrollbar-width: thin;
}

.batch-delete-item {
    display: grid;
    grid-template-columns: 28px 1fr auto;
    align-items: center;
    gap: 10px;
    min-height: 52px;
    padding: 8px 12px;
    transition: background-color 160ms;
}

.batch-delete-item + .batch-delete-item {
    border-top: 1px solid var(--color-border-subtle);
}

.batch-delete-item:hover {
    background: var(--color-surface-hover);
}

.batch-delete-item-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 7px;
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.batch-delete-item-name {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.batch-delete-item-room {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.batch-delete-more {
    border-top: 1px dashed var(--color-border);
    padding: 10px 14px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
    text-align: center;
}

/* ── 批量删除进度条 ───────────────────────────────────────────── */
.batch-delete-progress {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    min-height: 150px;
    justify-content: center;
    border: 1px solid var(--color-danger-border);
    border-radius: 12px;
    padding: 20px;
    background: var(--color-danger-soft);
}

.batch-delete-progress-bar {
    width: 100%;
    height: 4px;
    overflow: hidden;
    border-radius: 999px;
    background: var(--color-surface-subtle);
}

.batch-delete-progress-fill {
    width: 30%;
    height: 100%;
    border-radius: 999px;
    background: var(--color-danger);
    animation: batch-delete-progress-indeterminate 1.2s ease-in-out infinite;
}

@keyframes batch-delete-progress-indeterminate {
    from {
        transform: translateX(-100%);
    }
    to {
        transform: translateX(400%);
    }
}

.batch-delete-progress-label {
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-secondary);
}

@media (prefers-reduced-motion: reduce) {
    .batch-delete-progress-fill {
        animation-duration: 2s;
    }
}

.batch-delete-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 14px 22px;
    border-top: 1px solid var(--color-border-subtle);
    background: var(--color-workspace-background);
}

.batch-delete-footer div {
    display: flex;
    flex-shrink: 0;
    gap: 10px;
}

.batch-delete-footer span {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.batch-delete-cancel,
.batch-delete-confirm {
    display: inline-flex;
    height: 38px;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border-radius: 9px;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 900;
}

.batch-delete-cancel {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.batch-delete-confirm {
    border: 1px solid var(--color-danger);
    background: var(--color-danger);
    color: var(--color-text-on-primary);
    box-shadow: 0 6px 16px var(--color-danger-soft);
}

.batch-delete-confirm:disabled svg {
    animation: batch-delete-spin 900ms linear infinite;
}

@keyframes batch-delete-spin {
    to {
        transform: rotate(360deg);
    }
}

/* ── 日志查看弹窗 ───────────────────────────────────────────────────── */

.log-dialog-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 24px;
    border-bottom: 1px solid var(--color-border);
    background: linear-gradient(
        180deg,
        var(--color-card-bg) 60%,
        var(--color-primary-50)
    );
}

.log-dialog-icon {
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50));
    color: var(--color-primary-600);
    box-shadow: 0 2px 8px var(--color-focus-ring);
}

.log-dialog-icon svg {
    width: 24px;
    height: 24px;
}

.log-dialog-header h2,
.log-dialog-subtitle {
    margin: 0;
}

.log-dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 22px;
    font-weight: 900;
    line-height: 1.3;
}

.log-dialog-subtitle {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 6px;
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 700;
}

.log-count-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 22px;
    border-radius: 11px;
    background: var(--color-primary-100);
    padding: 0 7px;
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 900;
    line-height: 1;
}

.log-dialog-close {
    display: grid;
    width: 36px;
    height: 36px;
    margin-left: auto;
    place-items: center;
    border-radius: 10px;
    color: var(--color-text-tertiary);
    transition: background-color 160ms, color 160ms;
}

.log-dialog-close:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.log-dialog-body {
    max-height: 480px;
    overflow-y: auto;
    padding: 20px 24px 16px;
}

.log-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    min-height: 140px;
    justify-content: center;
    color: var(--color-text-tertiary);
    font-size: 15px;
    font-weight: 700;
}

.log-empty svg {
    width: 40px;
    height: 40px;
    opacity: 0.4;
}

/* ── 时间线布局 ── */

.log-timeline {
    display: grid;
    gap: 0;
}

.log-item {
    display: grid;
    grid-template-columns: 20px 1fr;
    gap: 14px;
    animation: log-item-enter 240ms ease both;
}

@keyframes log-item-enter {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ── 时间线节点 ── */

.log-timeline-node {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.log-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--color-border);
    flex-shrink: 0;
    box-shadow: 0 0 0 3px var(--color-card-bg);
    z-index: 1;
    transition: transform 200ms;
}

.log-item:hover .log-dot {
    transform: scale(1.3);
}

.log-dot.is-create {
    background: var(--color-success);
}

.log-dot.is-update {
    background: var(--color-primary-500);
}

.log-dot.is-sync {
    background: var(--color-warning);
}

.log-dot.is-group {
    background: var(--color-purple-500);
}

.log-dot.is-delete {
    background: var(--color-danger);
}

.log-line {
    width: 2px;
    flex: 1;
    min-height: 12px;
    border-radius: 1px;
    background: var(--color-border);
    opacity: 0.6;
}

.log-line.is-create { background: var(--color-success); opacity: 0.3; }
.log-line.is-update { background: var(--color-primary-500); opacity: 0.3; }
.log-line.is-sync { background: var(--color-warning); opacity: 0.3; }
.log-line.is-group { background: var(--color-purple-500); opacity: 0.3; }
.log-line.is-delete { background: var(--color-danger); opacity: 0.3; }

/* ── 日志卡片 ── */

.log-card {
    display: grid;
    gap: 6px;
    margin-bottom: 12px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 14px 16px;
    transition: box-shadow 200ms, border-color 200ms, transform 200ms;
}

.log-card:hover {
    border-color: var(--color-primary-200);
    box-shadow: 0 4px 16px var(--color-focus-ring);
    transform: translateY(-1px);
}

.log-card.is-create {
    border-left: 3px solid var(--color-success);
}

.log-card.is-update {
    border-left: 3px solid var(--color-primary-500);
}

.log-card.is-sync {
    border-left: 3px solid var(--color-warning);
}

.log-card.is-group {
    border-left: 3px solid var(--color-purple-500);
}

.log-card.is-delete {
    border-left: 3px solid var(--color-danger);
}

.log-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.log-action-label {
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
    line-height: 1.4;
}

.log-time {
    flex-shrink: 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
}

.log-message {
    margin: 0;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 600;
    line-height: 1.5;
    text-overflow: ellipsis;
}
</style>
