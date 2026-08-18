<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import type { SecurityDevice } from "../../types/settings";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import ConfirmActionDialog from "../common/ConfirmActionDialog.vue";
import ConfirmEntitySummary from "../common/ConfirmEntitySummary.vue";
import { useSettingsStore } from "../../stores/settings";

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
const pendingRevokeDevice = ref<SecurityDevice | null>(null);

const closeDialog = () => {
    emit("update:modelValue", false);
};

const toggleDeviceTrust = (deviceId: number, trusted: boolean) => {
    settingsStore.updateDeviceTrust(deviceId, trusted);
};

const revokeDevice = (deviceId: number) => {
    const device = devices.value.find((item) => item.id === deviceId);
    if (!device || device.current) return;
    pendingRevokeDevice.value = device;
};

const confirmRevoke = () => {
    const device = pendingRevokeDevice.value;
    if (!device) return;
    settingsStore.revokeSecurityDevice(device.id);
    pendingRevokeDevice.value = null;
    ElMessage.success("设备已移除");
};
</script>

<template>
    <BaseSmartModal
        :model-value="props.modelValue"
        width="large"
        title="登录设备管理"
        description="管理当前账户已记录的登录设备"
        icon="device-management"
        tone="teal"
        body-tone="neutral"
        @update:model-value="emit('update:modelValue', $event)"
    >

        <div class="device-dialog-body">
            <section class="device-list-card">
                <div class="device-card-header">
                    <div>
                        <strong>设备列表</strong>
                        <span>{{ devices.length }} 台设备</span>
                    </div>
                </div>

                <div class="device-list">
                    <article
                        v-for="device in devices"
                        :key="device.id"
                        class="device-item"
                    >
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
                                    @click="
                                        toggleDeviceTrust(
                                            device.id,
                                            !device.trusted,
                                        )
                                    "
                                >
                                    {{
                                        device.trusted ? "取消信任" : "设为信任"
                                    }}
                                </button>
                                <BaseButton
                                    :disabled="device.current"
                                    variant="danger"
                                    plain
                                    @click="revokeDevice(device.id)"
                                >
                                    移除
                                </BaseButton>
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
                    <BaseButton variant="primary" @click="closeDialog"
                        >关闭</BaseButton
                    >
                </div>
            </footer>
        </template>
    </BaseSmartModal>

    <ConfirmActionDialog
        v-if="pendingRevokeDevice"
        :model-value="true"
        title="移除登录设备"
        description="移除后，该设备将无法再访问当前账户。"
        confirm-text="移除"
        warning="移除后需重新登录才能恢复访问。"
        @confirm="confirmRevoke"
        @update:model-value="!$event && (pendingRevokeDevice = null)"
    >
        <ConfirmEntitySummary
            icon="device-management"
            :title="pendingRevokeDevice.name"
            :description="pendingRevokeDevice.location"
            color="var(--color-danger)"
        />
    </ConfirmActionDialog>
</template>

<style scoped>
.dialog-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 17px 20px 14px;
    border-bottom: 1px solid var(--color-divider);
    background: linear-gradient(
        135deg,
        var(--color-dialog-header-start),
        var(--color-dialog-header-end)
    );
}

.dialog-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 11px;
    color: white;
    background: linear-gradient(
        135deg,
        var(--color-dialog-icon-start),
        var(--color-dialog-icon-end)
    );
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
    gap: 18px;
    padding: 0;
}

.device-list-card,
.device-summary {
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.device-list-card,
.device-summary {
    padding: 16px;
}

.device-card-header {
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border);
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
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-surface-subtle);
    transition:
        border-color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.device-item:hover {
    border-color: var(--color-teal-border);
    background: var(--tone-teal-soft);
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
    color: var(--tone-teal);
    background: var(--tone-teal-soft);
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
    border-color: var(--color-teal-border);
    background: linear-gradient(
        160deg,
        var(--color-card-bg),
        var(--tone-teal-soft)
    );
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
