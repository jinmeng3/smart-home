<script setup lang="ts">
import { computed } from "vue";
import BaseButton from "../common/BaseButton.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import { useSettingsStore } from "../../stores/settings";

const props = defineProps<{
    modelValue: boolean;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const settingsStore = useSettingsStore();
const logs = computed(() => settingsStore.securityMeta.logs);

const closeDialog = () => {
    emit("update:modelValue", false);
};
</script>

<template>
    <BaseSmartModal
        :model-value="props.modelValue"
        width="medium"
        title="操作日志"
        description="查看最近的本地安全变更"
        icon="log"
        tone="primary"
        @update:model-value="emit('update:modelValue', $event)"
    >

        <div class="logs-dialog-body">
            <section class="logs-card">
                <div class="logs-card-header">
                    <div>
                        <strong>安全记录</strong>
                        <span>最近 {{ logs.length }} 条</span>
                    </div>
                </div>

                <div class="log-list">
                    <article v-for="log in logs" :key="log.id" class="log-item">
                        <div class="log-marker" aria-hidden="true" />
                        <div>
                            <div class="log-head">
                                <strong>{{ log.title }}</strong>
                                <span>{{ log.at }}</span>
                            </div>
                            <p>{{ log.detail }}</p>
                        </div>
                    </article>
                    <p v-if="logs.length === 0" class="empty-text">
                        暂无操作日志。
                    </p>
                </div>
            </section>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <span>日志仅保留最近 8 条</span>
                <div>
                    <BaseButton variant="primary" @click="closeDialog"
                        >关闭</BaseButton
                    >
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.dialog-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 17px 20px 14px;
    border-bottom: 1px solid var(--color-divider);
    background: linear-gradient(
        135deg,
        var(--color-dialog-header-start),
        var(--color-dialog-header-end)
    );
}

.dialog-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 11px;
    color: white;
    background: linear-gradient(
        135deg,
        var(--color-dialog-icon-start),
        var(--color-dialog-icon-end)
    );
}

.dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 17px;
    font-weight: 800;
}

.dialog-header p {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.close-button {
    margin: -4px -6px 0 auto;
    color: var(--color-text-tertiary);
    font-size: 22px;
}

.logs-dialog-body {
    gap: 18px;
    padding: 0;
}

.logs-card {
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    padding: 16px;
}

.logs-card-header {
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-border);
}

.logs-card-header strong,
.log-head strong {
    color: var(--color-text-primary);
    font-weight: 800;
}

.logs-card-header span,
.log-head span,
.log-item p,
.empty-text {
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.log-list {
    display: grid;
    gap: 10px;
}

.log-item {
    display: grid;
    grid-template-columns: 10px minmax(0, 1fr);
    gap: 12px;
    padding: 14px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-surface-subtle);
    transition:
        border-color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.log-item:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
}

.log-marker {
    width: 8px;
    height: 8px;
    margin-top: 5px;
    border-radius: 50%;
    background: var(--color-primary-600);
    box-shadow: 0 0 0 4px var(--color-focus-ring);
}

.log-head,
.dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.log-item p {
    margin-top: 6px;
    line-height: 1.5;
}

.dialog-footer {
    padding: 12px 20px;
    border-top: 1px solid var(--color-divider);
    background: var(--color-workspace-background);
}

.dialog-footer > span {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

@media (max-width: 640px) {
    .log-head,
    .dialog-footer {
        align-items: stretch;
        flex-direction: column;
    }

    .dialog-footer > div {
        display: flex;
        justify-content: flex-end;
    }
}
</style>
