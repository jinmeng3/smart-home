<script setup lang="ts">
import { ref } from "vue";
import type { SecuritySettings } from "../../types/settings";
import BaseSwitch from "../BaseSwitch.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import SettingsField from "./SettingsField.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { defineAsyncDialog, preloadDialog } from "../../utils/asyncDialog";

const loadChangePasswordDialog = () => import("./ChangePasswordDialog.vue");
const loadDeviceManagementDialog = () => import("./DeviceManagementDialog.vue");
const loadSecurityLogsDialog = () => import("./SecurityLogsDialog.vue");

const ChangePasswordDialog = defineAsyncDialog(loadChangePasswordDialog);
const DeviceManagementDialog = defineAsyncDialog(loadDeviceManagementDialog);
const SecurityLogsDialog = defineAsyncDialog(loadSecurityLogsDialog);

defineProps<{
    security: SecuritySettings;
}>();

const passwordDialogVisible = ref(false);
const devicesDialogVisible = ref(false);
const logsDialogVisible = ref(false);
</script>

<template>
    <SettingsSectionCard id="security" icon="security" title="安全" tone="danger">
        <div class="grid gap-2">
            <SettingsField icon="key" label="修改密码" description="定期更新密码，保护账户安全" tone="danger">
                <button
                    class="sf-secondary-btn"
                    type="button"
                    @focus="preloadDialog(loadChangePasswordDialog)"
                    @mouseenter="preloadDialog(loadChangePasswordDialog)"
                    @click="passwordDialogVisible = true"
                >
                    修改密码 <SvgIcon name="chevron-right" size="sm" />
                </button>
            </SettingsField>
            <SettingsField icon="fingerprint" label="双重认证" :description="security.twoFactorEnabled ? '额外验证保护已开启' : '建议开启额外身份验证'" tone="danger">
                <BaseSwitch v-model="security.twoFactorEnabled" />
            </SettingsField>
            <SettingsField icon="smartphone" label="登录设备" description="查看并管理已记录的登录终端" tone="danger">
                <button
                    class="sf-secondary-btn"
                    type="button"
                    @focus="preloadDialog(loadDeviceManagementDialog)"
                    @mouseenter="preloadDialog(loadDeviceManagementDialog)"
                    @click="devicesDialogVisible = true"
                >
                    管理设备 <SvgIcon name="chevron-right" size="sm" />
                </button>
            </SettingsField>
            <SettingsField icon="log" label="操作日志" description="追踪近期账户安全变更" tone="danger">
                <button
                    class="sf-secondary-btn"
                    type="button"
                    @focus="preloadDialog(loadSecurityLogsDialog)"
                    @mouseenter="preloadDialog(loadSecurityLogsDialog)"
                    @click="logsDialogVisible = true"
                >
                    查看日志 <SvgIcon name="chevron-right" size="sm" />
                </button>
            </SettingsField>
        </div>

        <ChangePasswordDialog
            v-if="passwordDialogVisible"
            v-model="passwordDialogVisible"
        />
        <DeviceManagementDialog
            v-if="devicesDialogVisible"
            v-model="devicesDialogVisible"
        />
        <SecurityLogsDialog
            v-if="logsDialogVisible"
            v-model="logsDialogVisible"
        />
    </SettingsSectionCard>
</template>

<style scoped>
.sf-secondary-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    min-width: 88px;
    justify-content: center;
    height: 30px;
    border-radius: 8px;
    padding: 0 12px;
    font-size: 12px;
    font-weight: 800;
    color: var(--color-danger);
    transition:
        background-color 160ms var(--motion-ease);
}

.sf-secondary-btn:hover {
    background: var(--color-danger-soft);
}
</style>