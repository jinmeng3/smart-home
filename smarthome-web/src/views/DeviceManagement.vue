<script setup lang="ts">
import { onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import BaseSmartModal from "../components/common/BaseSmartModal.vue";
import ConfirmActionDialog from "../components/common/ConfirmActionDialog.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import DeviceDetail from "../components/device/DeviceDetail.vue";
import DeviceList from "../components/device/DeviceList.vue";
import DeviceQuickActions from "../components/device/DeviceQuickActions.vue";
import DeviceStatsCard from "../components/device/DeviceStatsCard.vue";
import DeviceToolbar from "../components/device/DeviceToolbar.vue";
import PlatformStatus from "../components/device/PlatformStatus.vue";
import { useDeviceManagementController } from "../composables/useDeviceManagementController";
import { useAuthStore } from "../stores/auth";
import { defineAsyncDialog } from "../utils/asyncDialog";

const DeviceEditorDialog = defineAsyncDialog(
    () => import("../components/device/DeviceEditorDialog.vue"),
);

const controller = useDeviceManagementController();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const loadDevicesIfAuthenticated = () => {
    if (!authStore.isAuthenticated) {
        authStore.openLogin();
        return;
    }
    void controller.loadDevices();
};

watch(
    () => [
        controller.filters.page,
        controller.filters.pageSize,
        controller.filters.keyword,
        controller.filters.type,
        controller.filters.status,
        controller.filters.room,
    ],
    () => {
        loadDevicesIfAuthenticated();
    },
);

onMounted(() => {
    // Read view parameter from URL
    const view = route.query.view as "all" | "frequent" | "favorite" | undefined;
    if (view === "frequent" || view === "favorite") {
        controller.setViewMode(view);
    }
    loadDevicesIfAuthenticated();
});
</script>

<template>
    <div class="app-page-layout">
        <section class="device-management-page page-shell page-enter">
            <header class="device-page-header">
                <div class="device-page-title">
                    <h1>设备管理</h1>
                    <p>统一管理家庭设备、状态、分组与接入平台</p>
                </div>

                <DeviceToolbar
                    :keyword="controller.filters.keyword"
                    :room="controller.filters.room"
                    :rooms="controller.rooms.value"
                    :status="controller.filters.status"
                    :type="controller.filters.type"
                    @update:keyword="(value) => controller.updateFilter('keyword', value)"
                    @update:room="(value) => controller.updateFilter('room', value)"
                    @update:status="(value) => controller.updateFilter('status', value)"
                    @update:type="(value) => controller.updateFilter('type', value)"
                />
            </header>

            <div class="device-stats-grid">
                <DeviceStatsCard
                    icon="online-device"
                    label="在线设备"
                    :value="controller.stats.value.online"
                    tone="success"
                    :delay="0"
                    style="animation-delay: 0ms"
                />
                <DeviceStatsCard
                    icon="offline-device"
                    label="离线设备"
                    :value="controller.stats.value.offline"
                    tone="muted"
                    :delay="60"
                    style="animation-delay: 60ms"
                />
                <DeviceStatsCard
                    icon="warning"
                    label="告警设备"
                    :value="controller.stats.value.warning"
                    tone="warning"
                    :delay="120"
                    style="animation-delay: 120ms"
                />
                <DeviceStatsCard
                    icon="new-device"
                    label="本月新增"
                    :value="controller.stats.value.monthlyNew"
                    tone="primary"
                    :delay="180"
                    style="animation-delay: 180ms"
                />
            </div>

            <DeviceList
                :active-type="controller.filters.type"
                :batch-mode="controller.batchMode.value"
                :selected-device-ids="controller.selectedDeviceIds.value"
                :devices="controller.sortedDevices.value"
                :loading="controller.loading.value"
                :page="controller.filters.page"
                :page-size="controller.filters.pageSize"
                :selected-id="controller.selectedId.value"
                :sort="controller.sort.value"
                :syncing="controller.syncing.value"
                :total="controller.total.value"
                @add="controller.addDevice"
                @batch="
                    controller.batchMode.value &&
                    controller.selectedDeviceIds.value.length
                        ? controller.batchDeleteDevices(controller.selectedDeviceIds.value)
                        : controller.toggleBatchMode()
                "
                @batch-select="controller.toggleSelectDevice"
                @edit="controller.editDevice"
                @remove="controller.removeDevice"
                @select="controller.selectDevice"
                @sync="controller.runSync"
                @update:active-type="(value) => controller.updateFilter('type', value)"
                @update:page="controller.updatePage"
                @update:page-size="controller.updatePageSize"
                @update:sort="controller.sort.value = $event"
            />
        </section>

        <aside class="device-right-panel">
            <DeviceDetail :device="controller.selectedDevice.value" />
            <DeviceQuickActions @action="controller.runQuickAction" />
            <PlatformStatus :platforms="controller.platforms.value" />
        </aside>

        <DeviceEditorDialog
            v-if="controller.editorOpen.value"
            v-model="controller.editorOpen.value"
            :device="controller.editingDevice.value"
            :loading="controller.saving.value"
            @submit="controller.saveDevice"
        />

        <ConfirmActionDialog
            v-if="controller.deleteDialogOpen.value"
            :loading="controller.deleting.value"
            :model-value="controller.deleteDialogOpen.value"
            title="删除设备"
            description="此操作会从设备管理中移除该设备。"
            warning="删除后将无法在设备列表、智能对话设备清单和快捷操作中继续管理该设备。"
            footer-hint="确认后会立即调用后端删除接口。"
            @cancel="controller.cancelRemoveDevice"
            @confirm="controller.confirmRemoveDevice"
            @update:model-value="controller.deleteDialogOpen.value = $event"
        >
            <section
                v-if="controller.deletingDevice.value"
                class="delete-dialog-body"
            >
                <div class="delete-device-summary">
                    <span class="delete-device-thumb" aria-hidden="true">
                        <SvgIcon name="device-management" />
                    </span>
                    <div>
                        <strong>{{
                            controller.deletingDevice.value.name
                        }}</strong>
                        <p>
                            {{ controller.deletingDevice.value.room }} ·
                            {{ controller.deletingDevice.value.brand }}
                        </p>
                    </div>
                </div>
            </section>
        </ConfirmActionDialog>

        <ConfirmActionDialog
            v-if="controller.batchDeleteDialogOpen.value"
            :loading="controller.batchDeleting.value"
            :model-value="controller.batchDeleteDialogOpen.value"
            title="批量删除设备"
            description="此操作会从设备管理中移除所选设备，不可撤销。"
            warning="所选设备的信息、关联日志及绑定关系会被一并删除。"
            footer-hint="确认后会立即调用后端删除接口。"
            @cancel="controller.cancelBatchDelete"
            @confirm="controller.confirmBatchDelete"
            @update:model-value="controller.batchDeleteDialogOpen.value = $event"
        >
            <section class="batch-delete-body">
                <div class="batch-delete-summary">
                    <div class="batch-delete-count">
                        <span class="batch-delete-number">{{ controller.batchDeletingIds.value.length }}</span>
                        <span class="batch-delete-unit">台设备</span>
                    </div>
                    <p class="batch-delete-hint">
                        将删除以下设备，包括设备信息、关联日志及绑定关系。
                    </p>
                </div>

                <div class="batch-delete-list">
                    <div
                        v-for="device in controller.batchDeletingDevices.value.slice(0, 6)"
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
                        v-if="controller.batchDeletingIds.value.length > 6"
                        class="batch-delete-more"
                    >
                        还有 {{ controller.batchDeletingIds.value.length - 6 }} 台设备
                    </div>
                </div>
            </section>

        </ConfirmActionDialog>

        <BaseSmartModal
            v-if="controller.logDialogOpen.value"
            :model-value="controller.logDialogOpen.value"
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
                            {{ controller.logDeviceName.value }}
                            <span class="log-count-badge">{{ controller.deviceLogs.value.length }}</span>
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
                <div
                    v-if="!controller.deviceLogs.value.length"
                    class="log-empty"
                >
                    <SvgIcon name="log" size="lg" />
                    <span>该设备暂无操作日志</span>
                </div>

                <div class="log-timeline">
                    <div
                        v-for="(log, index) in controller.deviceLogs.value"
                        :key="log.id"
                        class="log-item"
                        :style="{ '--i': index }"
                    >
                        <div class="log-timeline-node">
                            <span class="log-dot" :class="`is-${log.action}`"></span>
                            <div
                                v-if="index < controller.deviceLogs.value.length - 1"
                                class="log-line"
                                :class="`is-${log.action}`"
                            ></div>
                        </div>
                        <div class="log-card" :class="`is-${log.action}`">
                            <div class="log-card-top">
                                <span class="log-action-label">{{ controller.logActionLabel(log.action) }}</span>
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
    overflow: hidden;
    padding: 14px;
}

.device-page-header {
    display: grid;
    min-width: 0;
    grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
    gap: 24px;
    align-items: start;
}

.device-page-title {
    position: relative;
}

.device-page-title::after {
    content: '';
    position: absolute;
    right: 0;
    top: 6px;
    bottom: 6px;
    width: 1px;
    background: var(--color-border-subtle);
}

.device-page-title h1 {
    margin: 0;
    font-size: 26px;
    font-weight: 900;
    color: var(--color-text-primary);
    line-height: 1.15;
}

.device-page-title p {
    margin: 8px 0 0;
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 700;
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

.device-right-panel {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    border-left: 1px solid var(--color-border);
    background: var(--color-sidebar-bg);
    padding: 0 4px 0 14px;
}

.device-right-panel > * {
    animation: panel-enter 300ms var(--motion-ease) both;
}

.device-right-panel > *:nth-child(1) { animation-delay: 80ms; }
.device-right-panel > *:nth-child(2) { animation-delay: 160ms; }
.device-right-panel > *:nth-child(3) { animation-delay: 240ms; }

@keyframes panel-enter {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
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
    .device-page-header {
        grid-template-columns: 1fr;
    }

    .device-page-title::after {
        display: none;
    }

    .device-stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 720px) {
    .device-management-page {
        padding: 12px;
    }
    .device-stats-grid {
        grid-template-columns: 1fr;
    }
}

@media (prefers-reduced-motion: reduce) {
    .device-management-page {
        animation-duration: 1ms;
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
    gap: 16px;
    padding: 0;
}

.batch-delete-summary {
    display: grid;
    gap: 12px;
    padding: 20px 22px 0;
}

.batch-delete-count {
    display: flex;
    align-items: baseline;
    gap: 6px;
}

.batch-delete-number {
    font-size: 36px;
    font-weight: 900;
    color: var(--color-danger);
    line-height: 1;
}

.batch-delete-unit {
    font-size: 16px;
    font-weight: 900;
    color: var(--color-text-secondary);
}

.batch-delete-hint {
    margin: 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
    line-height: 1.6;
}

.batch-delete-list {
    display: grid;
    gap: 2px;
    margin: 0 22px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    overflow: hidden;
}

.batch-delete-item {
    display: grid;
    grid-template-columns: 28px 1fr auto;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
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
    background: var(--color-surface-subtle);
    color: var(--color-primary-700);
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
    animation: log-item-enter 300ms ease both;
    animation-delay: calc(var(--i, 0) * 40ms);
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
