<script setup lang="ts">
import { ref } from "vue";
import { ElButton, ElMessage } from "element-plus";
import BaseModal from "../common/BaseModal.vue";
import { useSettingsStore } from "../../stores/settings";
import type { BackupSettings, SettingsState } from "../../types/settings";
import BaseSwitch from "../BaseSwitch.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";

defineProps<{
    backup: BackupSettings;
}>();

const emit = defineEmits<{
    export: [];
    import: [settings: SettingsState];
}>();

const settingsStore = useSettingsStore();
const fileInput = ref<HTMLInputElement | null>(null);
const historyVisible = ref(false);

const selectBackupFile = () => {
    fileInput.value?.click();
};

const runBackup = (type: "manual" | "auto") => {
    settingsStore.recordBackup(
        type,
        type === "auto" ? "自动备份已写入本地记录" : "手动备份已写入本地记录",
    );
    ElMessage.success(type === "auto" ? "自动备份已完成" : "备份已完成");
};

const readBackupFile = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];

    if (!file) {
        return;
    }

    const reader = new FileReader();

    reader.onload = () => {
        try {
            emit("import", JSON.parse(String(reader.result)) as SettingsState);
            ElMessage.success("配置已导入");
        } catch {
            ElMessage.error("备份文件格式不正确");
        } finally {
            target.value = "";
        }
    };

    reader.readAsText(file);
};
</script>

<template>
    <SettingsSectionCard id="backup" icon="backup" title="备份恢复">
        <div class="settings-field">
            <span>导出配置</span>
            <button class="secondary-button" type="button" @click="emit('export')">
                导出
            </button>
        </div>
        <div class="settings-field">
            <span>导入备份</span>
            <button class="secondary-button" type="button" @click="selectBackupFile">
                导入
            </button>
            <input
                ref="fileInput"
                class="hidden"
                accept="application/json"
                type="file"
                @change="readBackupFile"
            />
        </div>
        <div class="settings-field">
            <span>自动备份</span>
            <BaseSwitch v-model="backup.autoBackup" />
        </div>
        <div class="settings-field">
            <span>最近备份时间</span>
            <strong class="text-sm font-semibold text-[var(--color-text-secondary)]">
                {{ backup.lastBackupTime }}
            </strong>
        </div>
        <div class="settings-field">
            <span>备份历史</span>
            <div class="flex gap-2">
                <button class="secondary-button" type="button" @click="runBackup('manual')">
                    立即备份
                </button>
                <button class="secondary-button" type="button" @click="historyVisible = true">
                    查看
                </button>
            </div>
        </div>

        <BaseModal
            v-model="historyVisible"
            :close-on-click-modal="true"
            :close-on-press-escape="true"
            :lock-scroll="true"
            :modal="true"
            :show-close="false"
            append-to-body
            class="account-family-dialog"
            modal-class="settings-dialog-overlay"
            width="620px"
        >
            <template #header>
                <header class="dialog-header">
                    <span class="dialog-icon" aria-hidden="true">○</span>
                    <div>
                        <h2>备份历史</h2>
                        <p>查看最近生成的本地备份记录</p>
                    </div>
                    <ElButton
                        aria-label="关闭"
                        class="close-button"
                        text
                        @click="historyVisible = false"
                        >×</ElButton
                    >
                </header>
            </template>

            <div class="backup-dialog-body">
                <section class="backup-panel backup-panel-actions">
                    <div class="backup-panel-heading">
                        <strong>备份操作</strong>
                        <span>本地执行</span>
                    </div>
                    <div class="backup-action-list">
                        <button class="backup-action" type="button" @click="runBackup('manual')">
                            <strong>立即备份</strong>
                            <span>创建一条手动记录</span>
                        </button>
                        <button
                            class="backup-action"
                            type="button"
                            @click="runBackup('auto')"
                        >
                            <strong>模拟自动备份</strong>
                            <span>按自动备份状态写入记录</span>
                        </button>
                        <button class="backup-action" type="button" @click="selectBackupFile">
                            <strong>导入备份</strong>
                            <span>从本地 JSON 恢复配置</span>
                        </button>
                    </div>
                </section>

                <aside class="backup-summary">
                    <div class="backup-summary-item">
                        <span>自动备份</span>
                        <strong>{{ backup.autoBackup ? "已开启" : "已关闭" }}</strong>
                    </div>
                    <div class="backup-summary-item">
                        <span>最近备份</span>
                        <strong>{{ backup.lastBackupTime }}</strong>
                    </div>
                    <div class="backup-summary-item">
                        <span>历史条数</span>
                        <strong>{{ settingsStore.backupHistory.length }} 条</strong>
                    </div>
                </aside>
            </div>

            <div class="backup-history-list">
                <div
                    v-for="item in settingsStore.backupHistory"
                    :key="item.id"
                    class="backup-history-item"
                >
                    <div class="backup-history-head">
                        <strong>
                            {{ item.type === "auto" ? "自动备份" : "手动备份" }}
                        </strong>
                        <span>{{ item.at }}</span>
                    </div>
                    <p>{{ item.note }}</p>
                </div>
            </div>

            <template #footer>
                <footer class="dialog-footer">
                    <span>立即备份会刷新最近备份时间</span>
                    <div>
                        <ElButton type="primary" @click="historyVisible = false">关闭</ElButton>
                    </div>
                </footer>
            </template>
        </BaseModal>

    </SettingsSectionCard>
</template>

<style scoped>
.backup-dialog-body {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 220px;
    gap: 16px;
    padding: 16px 20px 12px;
}

.backup-panel,
.backup-summary {
    min-width: 0;
    border: 1px solid var(--color-border-default);
    border-radius: 16px;
    background: var(--color-workspace-background);
}

.backup-panel {
    padding: 16px;
}

.backup-panel-heading {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
}

.backup-panel-heading strong {
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 800;
}

.backup-panel-heading span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.backup-action-list {
    display: grid;
    gap: 10px;
}

.backup-action {
    display: grid;
    justify-items: start;
    gap: 4px;
    padding: 13px 14px;
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-panel-background);
    text-align: left;
    transition:
        border-color 160ms ease,
        box-shadow 160ms ease,
        transform 120ms ease;
}

.backup-action:hover {
    border-color: var(--color-primary-300);
    box-shadow: 0 4px 12px var(--color-focus-ring);
    transform: translateY(-1px);
}

.backup-action strong {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.backup-action span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.backup-summary {
    display: grid;
    gap: 12px;
    align-content: start;
    padding: 16px;
}

.backup-summary-item {
    display: grid;
    gap: 4px;
}

.backup-summary-item span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.backup-summary-item strong {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.backup-history-list {
    display: grid;
    gap: 10px;
    padding: 0 20px 16px;
}

.backup-history-item {
    padding: 14px 16px;
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-panel-background);
}

.backup-history-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 6px;
}

.backup-history-head strong {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.backup-history-head span,
.backup-history-item p {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.backup-history-item p {
    line-height: 1.5;
}

@media (max-width: 640px) {
    .backup-dialog-body {
        grid-template-columns: 1fr;
    }
}
</style>
