<script setup lang="ts">
import { computed, useAttrs, useSlots } from "vue";
import { ElButton, ElDialog } from "element-plus";
import "element-plus/theme-chalk/el-button.css";
import "element-plus/theme-chalk/el-dialog.css";
import "element-plus/theme-chalk/el-overlay.css";

defineOptions({ inheritAttrs: false });

const props = withDefaults(
    defineProps<{
        modelValue: boolean;
        title?: string;
        description?: string;
        icon?: string;
        width?: string | number;
        showFooter?: boolean;
        confirmText?: string;
        cancelText?: string;
        loading?: boolean;
        closable?: boolean;
    }>(),
    {
        title: "",
        description: "",
        icon: "✦",
        width: "640px",
        showFooter: false,
        confirmText: "确认",
        cancelText: "取消",
        loading: false,
        closable: true,
    },
);

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    cancel: [];
    confirm: [];
}>();

const attrs = useAttrs();
const slots = useSlots();
const modalClass = computed(() => ["orion-base-modal", attrs.class]);
const overlayClass = computed(() =>
    ["orion-modal-overlay", attrs["modal-class"]]
        .filter((value): value is string => typeof value === "string")
        .join(" "),
);
const closeOnClickModal = computed(
    () =>
        props.closable &&
        !props.loading &&
        attrs["close-on-click-modal"] !== false,
);
const closeOnPressEscape = computed(
    () =>
        props.closable &&
        !props.loading &&
        attrs["close-on-press-escape"] !== false,
);

const close = () => {
    if (!props.closable || props.loading) return;
    emit("update:modelValue", false);
    emit("cancel");
};
</script>

<template>
    <ElDialog
        v-bind="attrs"
        :class="modalClass"
        :close-on-click-modal="closeOnClickModal"
        :close-on-press-escape="closeOnPressEscape"
        :draggable="false"
        :lock-scroll="true"
        :modal="true"
        :modal-class="overlayClass"
        :model-value="modelValue"
        :show-close="false"
        transition="dialog-fade"
        :width="width"
        append-to-body
        @update:model-value="emit('update:modelValue', $event)"
    >
        <template #header>
            <slot name="header">
                <header class="dialog-header">
                    <span class="dialog-icon" aria-hidden="true">{{
                        icon
                    }}</span>
                    <div>
                        <h2>{{ title }}</h2>
                        <p v-if="description">{{ description }}</p>
                    </div>
                    <ElButton
                        v-if="closable"
                        aria-label="关闭"
                        class="close-button"
                        :disabled="loading"
                        text
                        @click="close"
                        >×</ElButton
                    >
                </header>
            </slot>
        </template>

        <div class="orion-modal-content">
            <slot />
        </div>

        <template v-if="slots.footer || showFooter" #footer>
            <slot name="footer">
                <footer class="dialog-footer">
                    <span><slot name="footerHint" /></span>
                    <div>
                        <ElButton :disabled="loading" @click="close">{{
                            cancelText
                        }}</ElButton>
                        <ElButton
                            :loading="loading"
                            type="primary"
                            @click="emit('confirm')"
                        >
                            {{ confirmText }}
                        </ElButton>
                    </div>
                </footer>
            </slot>
        </template>
    </ElDialog>
</template>

<style>
.orion-base-modal {
    display: flex;
    max-width: calc(100vw - 32px);
    max-height: 80vh;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 18px;
    background: var(--color-panel-background);
    box-shadow: var(--shadow-card-hover);
    transform-origin: center;
    user-select: none;
}

.orion-modal-overlay {
    background: var(--color-overlay) !important;
    backdrop-filter: blur(6px);
}

.orion-base-modal .el-dialog__header,
.orion-base-modal .el-dialog__body,
.orion-base-modal .el-dialog__footer {
    padding: 0;
}

.orion-base-modal .el-dialog__body {
    min-height: 0;
    overflow-y: auto;
}

.el-dialog.orion-base-modal .dialog-header {
    display: flex;
    align-items: center;
    gap: 14px;
    cursor: default;
    padding: 18px 22px;
    border-bottom: 1px solid var(--color-border-subtle);
    background: linear-gradient(
        180deg,
        var(--color-card-bg),
        var(--color-page-bg)
    );
}

.el-dialog.orion-base-modal .dialog-icon,
.el-dialog.orion-base-modal .ai-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    color: var(--color-primary-700);
    font-size: 20px;
    background: var(--color-primary-50);
    box-shadow: none;
}

.el-dialog.orion-base-modal .dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 22px;
    font-weight: 700;
    line-height: 1.25;
}

.el-dialog.orion-base-modal .dialog-header p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 14px;
}

.orion-base-modal .close-button {
    margin-left: auto;
}

.orion-modal-content {
    padding: 22px;
}

.orion-base-modal .orion-modal-content > .current-account,
.orion-base-modal .orion-modal-content > .model-status {
    margin: 0 0 16px;
}

.orion-base-modal .orion-modal-content > .form-grid,
.orion-base-modal .orion-modal-content > .settings-grid,
.orion-base-modal .orion-modal-content > .device-dialog-body,
.orion-base-modal .orion-modal-content > .password-dialog-body,
.orion-base-modal .orion-modal-content > .backup-dialog-body,
.orion-base-modal .orion-modal-content > .logs-dialog-body {
    padding: 0;
}

.orion-base-modal .orion-modal-content > .member-toolbar {
    margin-top: 0;
}

.orion-base-modal .account-field,
.orion-base-modal .password-field,
.orion-base-modal .login-field {
    margin-bottom: 16px;
}

.orion-base-modal .dialog-footer {
    position: sticky;
    bottom: 0;
    padding: 14px 22px;
    border-top: 1px solid var(--color-border-subtle);
    background: var(--color-workspace-background);
}

.orion-base-modal .dialog-footer > div {
    gap: 12px;
}

.orion-base-modal .el-button:not(.close-button) {
    min-width: 88px;
    height: 40px;
    border-radius: 10px;
}

.orion-base-modal .el-button--danger.is-plain {
    border-color: var(--color-danger-border);
    color: var(--color-danger);
    background: var(--color-danger-soft);
}

.orion-base-modal input:not(.el-input__inner),
.orion-base-modal select,
.orion-base-modal .el-input__wrapper {
    min-height: 42px;
    border-color: var(--color-border);
    background: var(--color-card-bg);
}

.orion-base-modal .el-input__wrapper {
    border: 1px solid var(--color-border);
    box-shadow: none;
}

.orion-base-modal .el-input__wrapper:hover {
    border-color: var(--color-primary-300);
}

.orion-base-modal .el-input__wrapper.is-focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.orion-base-modal .el-input__inner,
.orion-base-modal .el-input__inner:focus {
    min-height: 0;
    border: 0;
    background: transparent;
    box-shadow: none !important;
    outline: 0;
}

.orion-base-modal input::placeholder,
.orion-base-modal textarea::placeholder {
    color: var(--color-text-muted);
}

.orion-base-modal label {
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 500;
}

.orion-base-modal .setting-card,
.orion-base-modal .current-account,
.orion-base-modal .device-list-card,
.orion-base-modal .device-summary,
.orion-base-modal .password-section,
.orion-base-modal .backup-option {
    border: 1px solid var(--color-border-default);
    border-radius: 16px;
    background: var(--color-surface-subtle);
}

.orion-status-badge {
    display: inline-flex;
    align-items: center;
    min-height: 26px;
    border-radius: 999px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 700;
}

.orion-status-badge.is-online {
    color: var(--color-success);
    background: var(--color-success-soft);
}
.orion-status-badge.is-warning {
    color: var(--color-warning);
    background: var(--color-warning-soft);
}
.orion-status-badge.is-error {
    color: var(--color-danger);
    background: var(--color-danger-soft);
}
.orion-status-badge.is-processing {
    color: var(--color-info);
    background: var(--color-info-soft);
}

.orion-base-modal .active-status,
.orion-base-modal .device-badge,
.orion-base-modal .password-strength-label {
    display: inline-flex;
    min-height: 26px;
    align-items: center;
    border-radius: 999px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 700;
}

.orion-base-modal .active-status,
.orion-base-modal .device-badge-current,
.orion-base-modal .device-badge-trusted {
    color: var(--color-success);
    background: var(--color-success-soft);
}

.orion-base-modal .device-badge-muted {
    color: var(--color-warning);
    background: var(--color-warning-soft);
}

.el-message-box {
    max-width: calc(100vw - 32px);
    border: 1px solid var(--color-border);
    border-radius: 20px;
    padding: 0;
    box-shadow: var(--shadow-card-hover);
}

.el-message-box__header {
    padding: 20px 24px 12px;
}
.el-message-box__title {
    font-size: 20px;
    font-weight: 700;
}
.el-message-box__content {
    padding: 12px 24px 24px;
    color: var(--color-text-secondary);
}
.el-message-box__btns {
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid var(--color-border-subtle);
}
.el-message-box__btns .el-button {
    height: 40px;
    margin: 0;
    border-radius: 10px;
}

@media (max-width: 640px) {
    .orion-base-modal {
        width: calc(100vw - 32px) !important;
        max-height: 90vh;
    }
}
</style>
