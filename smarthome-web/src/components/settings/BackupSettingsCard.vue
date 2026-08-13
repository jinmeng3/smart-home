<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { useSettingsStore } from "../../stores/settings";
import type { BackupSettings } from "../../types/settings";
import BaseSwitch from "../BaseSwitch.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import SettingsField from "./SettingsField.vue";
import { defineAsyncDialog } from "../../utils/asyncDialog";

const BackupHistoryDialog = defineAsyncDialog(
    () => import("./BackupHistoryDialog.vue"),
);

const props = defineProps<{
    backup: BackupSettings;
}>();

const settingsStore = useSettingsStore();
const historyVisible = ref(false);

const runBackup = (type: "manual" | "auto") => {
    settingsStore.recordBackup(
        type,
        type === "auto" ? "自动备份已写入本地记录" : "手动备份已写入本地记录",
    );
    ElMessage.success(type === "auto" ? "自动备份已完成" : "备份已完成");
};
</script>

<template>
    <SettingsSectionCard id="backup" icon="backup" title="备份恢复" tone="success">
        <div class="grid gap-2">
            <SettingsField icon="refresh" label="自动备份" :description="backup.autoBackup ? '保存设置时自动生成记录' : '自动备份当前已关闭'" tone="success">
                <BaseSwitch v-model="backup.autoBackup" />
            </SettingsField>
            <SettingsField icon="clock" label="最近备份" description="最后一次成功生成备份的时间" tone="success">
                <strong class="text-sm font-semibold text-[var(--color-text-secondary)] tabular-nums">
                    {{ backup.lastBackupTime }}
                </strong>
            </SettingsField>
            <SettingsField icon="backup" label="备份历史" :description="`共 ${settingsStore.backupHistory.length} 条本地记录`" tone="success">
                <div class="flex gap-2">
                    <button class="sf-secondary-btn" type="button" @click="runBackup('manual')">
                        立即备份
                    </button>
                    <button class="sf-secondary-btn" type="button" @click="historyVisible = true">
                        查看历史
                    </button>
                </div>
            </SettingsField>
        </div>

        <BackupHistoryDialog
            v-if="historyVisible"
            :backup="backup"
            @close="historyVisible = false"
        />
    </SettingsSectionCard>
</template>

<style scoped>
.sf-secondary-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    height: 30px;
    border-radius: 8px;
    padding: 0 12px;
    font-size: 12px;
    font-weight: 800;
    color: var(--color-primary-600);
    transition:
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.sf-secondary-btn:hover {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.tabular-nums {
    font-variant-numeric: tabular-nums;
}
</style>