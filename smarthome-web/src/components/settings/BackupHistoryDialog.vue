<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import { useSettingsStore } from "../../stores/settings";
import type { BackupSettings } from "../../types/settings";
import SvgIcon from "../common/SvgIcon.vue";

const props = defineProps<{
    backup: BackupSettings;
}>();

const emit = defineEmits<{
    close: [];
}>();

const settingsStore = useSettingsStore();
const visible = ref(true);

const close = () => {
    visible.value = false;
    emit("close");
};

const runBackup = (type: "manual" | "auto") => {
    settingsStore.recordBackup(
        type,
        type === "auto" ? "自动备份已写入本地记录" : "手动备份已写入本地记录",
    );
    ElMessage.success(type === "auto" ? "自动备份已完成" : "备份已完成");
};
</script>

<template>
    <BaseSmartModal
        :model-value="visible"
        width="620px"
        title="备份历史"
        description="查看最近生成的本地备份记录"
        icon="backup"
        tone="green"
        body-tone="neutral"
        @update:model-value="close"
    >
        <div class="backup-dialog-body">
            <section class="backup-panel backup-panel-actions">
                <div class="backup-panel-heading">
                    <strong>备份操作</strong>
                    <span>本地执行</span>
                </div>
                <div class="backup-action-list">
                    <button
                        class="backup-action"
                        type="button"
                        @click="runBackup('manual')"
                    >
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
                </div>
            </section>

            <aside class="backup-summary">
                <div class="backup-summary-item">
                    <span>自动备份</span>
                    <strong>{{
                        backup.autoBackup ? "已开启" : "已关闭"
                    }}</strong>
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
                    <BaseButton variant="primary" @click="close">关闭</BaseButton>
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.backup-dialog-body {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 220px;
    gap: 18px;
    padding: 0;
}

.backup-panel,
.backup-summary {
    min-width: 0;
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
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
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border);
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
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-surface-subtle);
    text-align: left;
    transition:
        border-color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.backup-action:hover {
    border-color: var(--color-success-border);
    background: var(--color-success-soft);
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
    border-color: var(--color-success-border);
    background: linear-gradient(
        160deg,
        var(--color-card-bg),
        var(--color-success-soft)
    );
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
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-surface-subtle);
    box-shadow: var(--shadow-card);
    transition:
        border-color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.backup-history-item:hover {
    border-color: var(--color-success-border);
    background: var(--color-success-soft);
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
