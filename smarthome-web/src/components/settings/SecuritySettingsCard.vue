<script setup lang="ts">
import { ref } from "vue";
import type { SecuritySettings } from "../../types/settings";
import BaseSwitch from "../BaseSwitch.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
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
        <div class="feature-list security-feature-list">
        <div class="feature-row">
            <span class="feature-icon"><SvgIcon name="lock" /></span>
            <span class="feature-copy"><strong>修改密码</strong><small>定期更新密码，保护账户安全</small></span>
            <button
                class="secondary-button"
                type="button"
                @focus="preloadDialog(loadChangePasswordDialog)"
                @mouseenter="preloadDialog(loadChangePasswordDialog)"
                @click="passwordDialogVisible = true"
            >
                修改密码 <SvgIcon name="chevron-right" size="sm" />
            </button>
        </div>
        <div class="feature-row">
            <span class="feature-icon"><SvgIcon name="security" /></span>
            <span class="feature-copy"><strong>双重认证</strong><small>{{ security.twoFactorEnabled ? "额外验证保护已开启" : "建议开启额外身份验证" }}</small></span>
            <BaseSwitch v-model="security.twoFactorEnabled" />
        </div>
        <div class="feature-row">
            <span class="feature-icon"><SvgIcon name="device-management" /></span>
            <span class="feature-copy"><strong>登录设备</strong><small>查看并管理已记录的登录终端</small></span>
            <button
                class="secondary-button"
                type="button"
                @focus="preloadDialog(loadDeviceManagementDialog)"
                @mouseenter="preloadDialog(loadDeviceManagementDialog)"
                @click="devicesDialogVisible = true"
            >
                管理设备 <SvgIcon name="chevron-right" size="sm" />
            </button>
        </div>
        <div class="feature-row">
            <span class="feature-icon"><SvgIcon name="log" /></span>
            <span class="feature-copy"><strong>操作日志</strong><small>追踪近期账户安全变更</small></span>
            <button
                class="secondary-button"
                type="button"
                @focus="preloadDialog(loadSecurityLogsDialog)"
                @mouseenter="preloadDialog(loadSecurityLogsDialog)"
                @click="logsDialogVisible = true"
            >
                查看日志 <SvgIcon name="chevron-right" size="sm" />
            </button>
        </div></div>

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
.feature-list { display: grid; gap: 8px; }
.feature-row { display: grid; min-height: 64px; grid-template-columns: 38px minmax(0, 1fr) auto; align-items: center; gap: 11px; border: 1px solid var(--color-border-subtle); border-radius: 13px; background: var(--color-surface-subtle); padding: 10px 12px; transition: border-color 160ms, transform 160ms, box-shadow 160ms; }
.feature-row:hover { transform: translateY(-1px); border-color: var(--color-danger-border); box-shadow: var(--shadow-card); }
.feature-icon { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 11px; background: var(--color-danger-soft); color: var(--color-danger); }
.feature-copy { display: grid; min-width: 0; gap: 2px; }
.feature-copy strong { color: var(--color-text-primary); font-size: 13px; font-weight: 850; }
.feature-copy small { overflow: hidden; color: var(--color-text-tertiary); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.secondary-button { display: inline-flex; align-items: center; gap: 4px; min-width: 88px; justify-content: center; }
</style>
