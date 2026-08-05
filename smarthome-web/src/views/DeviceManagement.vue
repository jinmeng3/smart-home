<script setup lang="ts">
import { onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import BaseSmartModal from "../components/common/BaseSmartModal.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import DeviceDetail from "../components/device/DeviceDetail.vue";
import DeviceEditorDialog from "../components/device/DeviceEditorDialog.vue";
import DeviceList from "../components/device/DeviceList.vue";
import DeviceQuickActions from "../components/device/DeviceQuickActions.vue";
import DeviceStatsCard from "../components/device/DeviceStatsCard.vue";
import DeviceToolbar from "../components/device/DeviceToolbar.vue";
import PlatformStatus from "../components/device/PlatformStatus.vue";
import { useDeviceManagementController } from "../composables/useDeviceManagementController";
import { useAuthStore } from "../stores/auth";

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
    <div class="contents">
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
                :devices="controller.sortedDevices.value"
                :loading="controller.loading.value"
                :page="controller.filters.page"
                :page-size="controller.filters.pageSize"
                :selected-id="controller.selectedId.value"
                :sort="controller.sort.value"
                :syncing="controller.syncing.value"
                :total="controller.total.value"
                @add="controller.addDevice"
                @batch="controller.runBatch"
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
            v-model="controller.editorOpen.value"
            :device="controller.editingDevice.value"
            :loading="controller.saving.value"
            @submit="controller.saveDevice"
        />

        <BaseSmartModal
            :closable="!controller.deleting.value"
            :loading="controller.deleting.value"
            :model-value="controller.deleteDialogOpen.value"
            width="520px"
            @update:model-value="
                $event
                    ? (controller.deleteDialogOpen.value = true)
                    : controller.cancelRemoveDevice()
            "
        >
            <template #header>
                <header class="delete-dialog-header">
                    <span class="delete-dialog-icon" aria-hidden="true">
                        <SvgIcon name="warning" />
                    </span>
                    <div>
                        <h2>删除设备</h2>
                        <p>此操作会从设备管理中移除该设备。</p>
                    </div>
                    <button
                        class="delete-dialog-close"
                        :disabled="controller.deleting.value"
                        type="button"
                        aria-label="关闭"
                        @click="controller.cancelRemoveDevice"
                    >
                        <SvgIcon name="close" size="sm" />
                    </button>
                </header>
            </template>

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
                <p class="delete-dialog-warning">
                    删除后将无法在设备列表、智能对话设备清单和快捷操作中继续管理该设备。
                </p>
            </section>

            <template #footer>
                <footer class="delete-dialog-footer">
                    <span>确认后会立即调用后端删除接口。</span>
                    <div>
                        <button
                            class="delete-cancel-button"
                            :disabled="controller.deleting.value"
                            type="button"
                            @click="controller.cancelRemoveDevice"
                        >
                            取消
                        </button>
                        <button
                            class="delete-confirm-button"
                            :disabled="controller.deleting.value"
                            type="button"
                            @click="controller.confirmRemoveDevice"
                        >
                            <SvgIcon
                                :name="
                                    controller.deleting.value
                                        ? 'refresh'
                                        : 'warning'
                                "
                                size="sm"
                            />
                            {{
                                controller.deleting.value
                                    ? "删除中"
                                    : "确认删除"
                            }}
                        </button>
                    </div>
                </footer>
            </template>
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
</style>
