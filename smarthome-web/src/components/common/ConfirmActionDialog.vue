<script setup lang="ts">
import BaseSmartModal from "./BaseSmartModal.vue";
import BaseButton from "./BaseButton.vue";
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
            <footer class="dialog-footer confirm-action-footer">
                <span>{{ footerHint }}</span>
                <div>
                    <BaseButton
                        :disabled="loading"
                        @click="close"
                    >
                        {{ cancelText }}
                    </BaseButton>
                    <BaseButton
                        variant="danger"
                        :loading="loading"
                        @click="emit('confirm')"
                    >
                        <SvgIcon v-if="!loading" name="warning" size="sm" />
                        {{ loading ? "处理中" : confirmText }}
                    </BaseButton>
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
    box-sizing: border-box;
}

.confirm-action-footer > span {
    color: var(--color-text-muted);
    font-size: 12px;
}

.confirm-action-footer > div {
    display: flex;
    gap: 10px;
}

</style>
