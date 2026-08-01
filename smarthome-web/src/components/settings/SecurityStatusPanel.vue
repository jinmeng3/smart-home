<script setup lang="ts">
import type {
    BackupSettings,
    NotificationSettings,
    SecuritySettings,
} from "../../types/settings";
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    security: SecuritySettings;
    backup: BackupSettings;
    notifications: NotificationSettings;
}>();
</script>

<template>
    <section
        class="motion-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-5"
    >
        <div class="mb-4 flex items-center gap-3">
            <span
                class="grid h-9 w-9 place-items-center rounded-lg bg-[var(--color-success-soft)] text-[var(--color-success)]"
            >
                <SvgIcon name="security" size="sm" />
            </span>
            <h2 class="text-base font-extrabold">安全状态</h2>
        </div>
        <div class="grid gap-4 text-sm">
            <div class="flex justify-between">
                <span>双重认证</span
                ><strong class="text-[var(--color-success)]">{{
                    security.twoFactorEnabled ? "已开启" : "未开启"
                }}</strong>
            </div>
            <div class="flex justify-between">
                <span>最近备份</span
                ><strong>{{ backup.lastBackupTime }}</strong>
            </div>
            <div class="flex justify-between">
                <span>通知状态</span
                ><strong>{{
                    notifications.securityAlerts ? "正常" : "已关闭"
                }}</strong>
            </div>
        </div>
    </section>
</template>
