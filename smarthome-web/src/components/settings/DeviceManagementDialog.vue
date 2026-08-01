<script setup lang="ts">
import { computed } from "vue";
import { ElButton, ElMessage, ElMessageBox } from "element-plus";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { useSettingsStore } from "../../stores/settings";
import "element-plus/theme-chalk/el-message-box.css";

const props = defineProps<{
    modelValue: boolean;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const settingsStore = useSettingsStore();
const devices = computed(() => settingsStore.securityMeta.devices);
const trustedDeviceCount = computed(
    () => devices.value.filter((device) => device.trusted).length,
);

const closeDialog = () => {
    emit("update:modelValue", false);
};

const toggleDeviceTrust = (deviceId: number, trusted: boolean) => {
    settingsStore.updateDeviceTrust(deviceId, trusted);
};

const revokeDevice = async (deviceId: number) => {
    const device = devices.value.find((item) => item.id === deviceId);

    if (!device || device.current) {
        return;
    }

    try {
        await ElMessageBox.confirm(`确认移除 ${device.name}？`, "移除登录设备", {
            confirmButtonText: "移除",
            cancelButtonText: "取消",
            type: "warning",
        });
        settingsStore.revokeSecurityDevice(deviceId);
        ElMessage.success("设备已移除");
    } catch {
        // User cancelled.
    }
};
</script>

<template>
    <BaseSmartModal
        :model-value="props.modelValue"
        :close-on-click-modal="true"
        :close-on-press-escape="true"
        :lock-scroll="true"
        :modal="true"
        :show-close="false"
        append-to-body
        class="account-family-dialog device-dialog"
        modal-class="settings-dialog-overlay"
        width="720px"
        @update:model-value="emit('update:modelValue', $event)"
    >
        <template #header>
            <header class="dialog-header">
                <span class="dialog-icon" aria-hidden="true">
                    <SvgIcon name="device-management" size="sm" />
                </span>
                <div>
                    <h2>登录设备管理</h2>
                    <p>管理当前账户已记录的登录设备</p>
                </div>
                <ElButton aria-label="关闭" class="close-button" text @click="closeDialog">
                    ×
                </ElButton>
            </header>
        </template>

        <div class="device-dialog-body">
            <section class="device-list-card">
                <div class="device-card-header">
                    <div>
                        <strong>设备列表</strong>
                        <span>{{ devices.length }} 台设备</span>
                    </div>
                </div>

                <div class="device-list">
                    <article v-for="device in devices" :key="device.id" class="device-item">
                        <div class="device-main">
                            <div>
                                <strong>{{ device.name }}</strong>
                                <span>{{ device.location }}</span>
                            </div>
                            <span
                                :class="[
                                    'device-badge',
                                    device.current
                                        ? 'device-badge-current'
                                        : device.trusted
                                          ? 'device-badge-trusted'
                                          : 'device-badge-muted',
                                ]"
                            >
                                {{
                                    device.current
                                        ? "当前设备"
                                        : device.trusted
                                          ? "已信任"
                                          : "未信任"
                                }}
                            </span>
                        </div>
                        <div class="device-footer">
                            <span>最近活跃 {{ device.lastActive }}</span>
                            <div>
                                <button
                                    class="secondary-button"
                                    type="button"
                                    @click="toggleDeviceTrust(device.id, !device.trusted)"
                                >
                                    {{ device.trusted ? "取消信任" : "设为信任" }}
                                </button>
                                <ElButton
                                    :disabled="device.current"
                                    plain
                                    type="danger"
                                    @click="revokeDevice(device.id)"
                                >
                                    移除
                                </ElButton>
                            </div>
                        </div>
                    </article>
                </div>
            </section>

            <aside class="device-summary">
                <div class="device-summary-item">
                    <span>可信设备</span>
                    <strong>{{ trustedDeviceCount }} 台</strong>
                </div>
                <div class="device-summary-item">
                    <span>总设备数</span>
                    <strong>{{ devices.length }} 台</strong>
                </div>
                <p>当前设备保留在列表中，无法移除。</p>
            </aside>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <span>设备信任状态只在本地更新</span>
                <div>
                    <ElButton type="primary" @click="closeDialog">关闭</ElButton>
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
:global(.device-dialog) {
    display: flex;
    max-height: calc(100vh - 48px);
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 20px;
    background: var(--color-panel-background);
    box-shadow: 0 24px 70px rgb(15 23 42 / 22%);
}

:global(.device-dialog .el-dialog__header),
:global(.device-dialog .el-dialog__body),
:global(.device-dialog .el-dialog__footer) {
    padding: 0;
}

:global(.device-dialog .el-dialog__body) {
    min-height: 0;
    overflow-y: auto;
}

.dialog-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 17px 20px 14px;
    border-bottom: 1px solid var(--color-divider);
    background: linear-gradient(135deg, var(--color-dialog-header-start), var(--color-dialog-header-end));
}

.dialog-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 11px;
    color: white;
    background: linear-gradient(135deg, var(--color-dialog-icon-start), var(--color-dialog-icon-end));
}

.dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 17px;
    font-weight: 800;
}

.dialog-header p {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.close-button {
    margin: -4px -6px 0 auto;
    color: var(--color-text-tertiary);
    font-size: 22px;
}

.device-dialog-body {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 220px;
    gap: 16px;
    padding: 16px 20px 18px;
}

.device-list-card,
.device-summary {
    min-width: 0;
    border: 1px solid var(--color-border-default);
    border-radius: 16px;
    background: var(--color-workspace-background);
}

.device-list-card,
.device-summary {
    padding: 16px;
}

.device-card-header {
    margin-bottom: 14px;
}

.device-card-header strong,
.device-item strong,
.device-summary-item strong {
    color: var(--color-text-primary);
    font-weight: 800;
}

.device-card-header span,
.device-main span,
.device-footer span,
.device-summary-item span,
.device-summary p {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.device-list {
    display: grid;
    gap: 10px;
}

.device-item {
    display: grid;
    gap: 12px;
    padding: 14px;
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-panel-background);
}

.device-main,
.device-footer,
.dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.device-main > div,
.device-summary,
.device-summary-item {
    display: grid;
    gap: 4px;
}

.device-footer > div,
.dialog-footer > div {
    display: flex;
    gap: 8px;
}

.device-badge {
    display: inline-flex;
    align-items: center;
    height: 24px;
    padding: 0 8px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
}

.device-badge-current {
    color: var(--color-primary-700);
    background: var(--color-primary-50);
}

.device-badge-trusted {
    color: var(--color-success);
    background: var(--color-success-soft);
}

.device-badge-muted {
    color: var(--color-text-tertiary);
    background: var(--color-surface-subtle);
}

.device-summary {
    align-content: start;
    gap: 12px;
}

.device-summary p {
    line-height: 1.5;
}

.dialog-footer {
    padding: 12px 20px;
    border-top: 1px solid var(--color-divider);
    background: var(--color-workspace-background);
}

.dialog-footer > span {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

@media (max-width: 640px) {
    :global(.device-dialog) {
        width: calc(100% - 24px) !important;
    }

    .device-dialog-body {
        grid-template-columns: 1fr;
    }

    .device-main,
    .device-footer,
    .dialog-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .device-footer > div,
    .dialog-footer > div {
        justify-content: flex-end;
    }
}
</style>
