<script setup lang="ts">
import type { NotificationSettings } from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import BaseSwitch from "../BaseSwitch.vue";
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    notifications: NotificationSettings;
}>();
</script>

<template>
    <SettingsSectionCard id="notifications" icon="bell-ring" title="通知" tone="warning">
        <div class="settings-field">
            <span class="settings-field-icon is-warning"><SvgIcon name="offline-device" size="sm" /></span>
            <span class="settings-field-label">设备离线通知</span
            ><BaseSwitch v-model="notifications.deviceOffline" />
        </div>
        <div class="settings-field">
            <span class="settings-field-icon is-warning"><SvgIcon name="warning" size="sm" /></span>
            <span class="settings-field-label">安防告警</span
            ><BaseSwitch v-model="notifications.securityAlerts" />
        </div>
        <div class="settings-field">
            <span class="settings-field-icon is-warning"><SvgIcon name="automation" size="sm" /></span>
            <span class="settings-field-label">自动化执行结果</span
            ><BaseSwitch v-model="notifications.automationResults" />
        </div>
        <div class="settings-field">
            <span class="settings-field-icon is-warning"><SvgIcon name="moon" size="sm" /></span>
            <span class="settings-field-label">免打扰时间</span>
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
