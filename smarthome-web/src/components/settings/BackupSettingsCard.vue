<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import { useSettingsStore } from "../../stores/settings";
import type { BackupSettings } from "../../types/settings";
import BaseSwitch from "../BaseSwitch.vue";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
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
        <div class="backup-feature-list">

        <div class="backup-feature-row">
            <span class="backup-feature-icon"><SvgIcon name="refresh" /></span>
            <span class="backup-feature-copy"><strong>自动备份</strong><small>{{ backup.autoBackup ? "保存设置时自动生成记录" : "自动备份当前已关闭" }}</small></span>
            <BaseSwitch v-model="backup.autoBackup" />
        </div>
        <div class="backup-feature-row backup-time-row">
            <span class="backup-feature-icon"><SvgIcon name="clock" /></span>
            <span class="backup-feature-copy"><strong>最近备份</strong><small>最后一次成功生成备份的时间</small></span>
            <strong
                class="text-sm font-semibold text-[var(--color-text-secondary)]"
            >
                {{ backup.lastBackupTime }}
            </strong>
        </div>
        <div class="backup-feature-row">
            <span class="backup-feature-icon"><SvgIcon name="backup" /></span>
            <span class="backup-feature-copy"><strong>备份历史</strong><small>共 {{ settingsStore.backupHistory.length }} 条本地记录</small></span>
            <div class="flex gap-2">
                <button
                    class="secondary-button"
                    type="button"
                    @click="runBackup('manual')"
                >
                    立即备份
                </button>
                <button
                    class="secondary-button"
                    type="button"
                    @click="historyVisible = true"
                >
                    查看历史
                </button>
            </div>
        </div></div>

        <BaseSmartModal
            v-model="historyVisible"
            width="620px"
            title="备份历史"
            description="查看最近生成的本地备份记录"
            icon="backup"
            tone="green"
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
                        <strong
                            >{{ settingsStore.backupHistory.length }} 条</strong
                        >
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
                        <BaseButton variant="primary" @click="historyVisible = false"
                            >关闭</BaseButton
                        >
                    </div>
                </footer>
            </template>
        </BaseSmartModal>
    </SettingsSectionCard>
</template>

<style scoped>
.backup-feature-list { display: grid; gap: 8px; }
.backup-feature-row { display: grid; min-height: 62px; grid-template-columns: 38px minmax(0, 1fr) auto; align-items: center; gap: 11px; border: 1px solid var(--color-border-subtle); border-radius: 13px; background: var(--color-surface-subtle); padding: 10px 12px; transition: border-color 160ms, transform 160ms, box-shadow 160ms; }
.backup-feature-row:hover { transform: translateY(-1px); border-color: color-mix(in srgb, var(--color-success) 32%, var(--color-border)); box-shadow: var(--shadow-card); }
.backup-feature-icon { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 11px; background: var(--color-success-soft); color: var(--color-success); }
.backup-feature-copy { display: grid; min-width: 0; gap: 2px; }
.backup-feature-copy strong { color: var(--color-text-primary); font-size: 13px; font-weight: 850; }
.backup-feature-copy small { overflow: hidden; color: var(--color-text-tertiary); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.backup-feature-row .secondary-button { display: inline-flex; align-items: center; justify-content: center; gap: 4px; }
.backup-time-row > strong { border-radius: 9px; background: var(--color-card-bg); padding: 6px 9px; font-variant-numeric: tabular-nums; }
.backup-feature-row > .flex { flex-wrap: wrap; justify-content: flex-end; }

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
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
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
    border-color: var(--color-primary-200);
    background: linear-gradient(
        160deg,
        var(--color-card-bg),
        var(--color-primary-50)
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
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
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
