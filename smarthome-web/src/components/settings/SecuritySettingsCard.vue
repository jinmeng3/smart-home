<script setup lang="ts">
import { ref } from "vue";
import type { SecuritySettings } from "../../types/settings";
import BaseSwitch from "../BaseSwitch.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
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
        <div class="settings-field">
            <span>修改密码</span>
            <button
                class="secondary-button"
                type="button"
                @focus="preloadDialog(loadChangePasswordDialog)"
                @mouseenter="preloadDialog(loadChangePasswordDialog)"
                @click="passwordDialogVisible = true"
            >
                修改
            </button>
        </div>
        <div class="settings-field">
            <span>双重认证</span>
            <BaseSwitch v-model="security.twoFactorEnabled" />
        </div>
        <div class="settings-field">
            <span>登录设备管理</span>
            <button
                class="secondary-button"
                type="button"
                @focus="preloadDialog(loadDeviceManagementDialog)"
                @mouseenter="preloadDialog(loadDeviceManagementDialog)"
                @click="devicesDialogVisible = true"
            >
                管理
            </button>
        </div>
        <div class="settings-field">
            <span>操作日志</span>
            <button
                class="secondary-button"
                type="button"
                @focus="preloadDialog(loadSecurityLogsDialog)"
                @mouseenter="preloadDialog(loadSecurityLogsDialog)"
                @click="logsDialogVisible = true"
            >
                查看
            </button>
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
