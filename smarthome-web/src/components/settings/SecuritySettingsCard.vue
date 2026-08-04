<script setup lang="ts">
import { ref } from "vue";
import type { SecuritySettings } from "../../types/settings";
import BaseSwitch from "../BaseSwitch.vue";
import ChangePasswordDialog from "./ChangePasswordDialog.vue";
import DeviceManagementDialog from "./DeviceManagementDialog.vue";
import SecurityLogsDialog from "./SecurityLogsDialog.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";

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
                @click="logsDialogVisible = true"
            >
                查看
            </button>
        </div>

        <ChangePasswordDialog v-model="passwordDialogVisible" />
        <DeviceManagementDialog v-model="devicesDialogVisible" />
        <SecurityLogsDialog v-model="logsDialogVisible" />
    </SettingsSectionCard>
</template>
