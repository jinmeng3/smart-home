<script setup lang="ts">
import BaseSmartModal from "./BaseSmartModal.vue";
import SvgIcon from "./SvgIcon.vue";

withDefaults(
    defineProps<{
        modelValue: boolean;
        title: string;
        description: string;
        confirmText?: string;
        cancelText?: string;
        loading?: boolean;
        warning?: string;
        footerHint?: string;
    }>(),
    {
        confirmText: "确认删除",
        cancelText: "取消",
        loading: false,
        warning: "删除后无法恢复，请谨慎操作。",
        footerHint: "此操作不可撤销",
    },
);

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    confirm: [];
    cancel: [];
}>();

const close = () => {
    emit("update:modelValue", false);
    emit("cancel");
};
</script>

<template>
    <BaseSmartModal
        :closable="!loading"
        :loading="loading"
        :model-value="modelValue"
        :title="title"
        :description="description"
        icon="warning"
        width="520px"
        @confirm="emit('confirm')"
        @update:model-value="$event ? undefined : close()"
    >
        <div class="confirm-action-summary">
            <slot />
        </div>

        <template #warning>
            <p class="confirm-action-warning">
                <SvgIcon name="warning" size="sm" />
                {{ warning }}
            </p>
        </template>

        <template #footer>
            <footer class="confirm-action-footer">
                <span>{{ footerHint }}</span>
                <div>
                    <button
                        class="confirm-action-cancel"
                        :disabled="loading"
                        type="button"
                        @click="close"
                    >
                        {{ cancelText }}
                    </button>
                    <button
                        class="confirm-action-confirm"
                        :disabled="loading"
                        type="button"
                        @click="emit('confirm')"
                    >
                        <SvgIcon :name="loading ? 'refresh' : 'warning'" size="sm" />
                        {{ loading ? "处理中" : confirmText }}
                    </button>
                </div>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.confirm-action-summary {
    display: grid;
    gap: 14px;
}

.confirm-action-warning {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
}

.confirm-action-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    width: 100%;
}

.confirm-action-footer > span {
    color: var(--color-text-muted);
    font-size: 12px;
}

.confirm-action-footer > div {
    display: flex;
    gap: 10px;
}

.confirm-action-cancel,
.confirm-action-confirm {
    display: inline-flex;
    min-height: 38px;
    align-items: center;
    justify-content: center;
    gap: 7px;
    padding: 0 18px;
    border-radius: 10px;
    font-weight: 700;
}

.confirm-action-cancel {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.confirm-action-confirm {
    border: 1px solid var(--color-danger, #ef4444);
    background: var(--color-danger, #ef4444);
    color: #fff;
}

.confirm-action-cancel:disabled,
.confirm-action-confirm:disabled {
    cursor: not-allowed;
    opacity: 0.6;
}
</style>
