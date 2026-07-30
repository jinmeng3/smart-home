<script setup lang="ts">
import type { NotificationSettings } from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";

defineProps<{
    notifications: NotificationSettings;
}>();
</script>

<template>
    <SettingsSectionCard id="notifications" icon="♙" title="通知">
        <div class="settings-field">
            <span>设备离线通知</span
            ><el-switch v-model="notifications.deviceOffline" />
        </div>
        <div class="settings-field">
            <span>安防告警</span
            ><el-switch v-model="notifications.securityAlerts" />
        </div>
        <div class="settings-field">
            <span>自动化执行结果</span
            ><el-switch v-model="notifications.automationResults" />
        </div>
        <div class="settings-field">
            <span>免打扰时间</span>
            <div class="flex min-w-[220px] items-center justify-end gap-2">
                <input
                    v-model="notifications.quietStart"
                    class="settings-input time-input"
                    type="time"
                />
                <span class="text-[var(--color-text-tertiary)]">-</span>
                <input
                    v-model="notifications.quietEnd"
                    class="settings-input time-input"
                    type="time"
                />
            </div>
        </div>
    </SettingsSectionCard>
</template>
