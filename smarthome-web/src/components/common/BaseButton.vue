<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "./SvgIcon.vue";

const props = withDefaults(
    defineProps<{
        variant?: "default" | "primary" | "danger" | "warning" | "text";
        size?: "sm" | "md";
        plain?: boolean;
        /** 占满父容器宽度 */
        block?: boolean;
        loading?: boolean;
        disabled?: boolean;
        nativeType?: "button" | "submit" | "reset";
        /** 操作结果反馈：成功后短暂显示 check / 失败显示 warning（替换 spinner） */
        feedback?: "success" | "error" | null;
    }>(),
    {
        variant: "default",
        size: "md",
        plain: false,
        block: false,
        loading: false,
        disabled: false,
        nativeType: "button",
        feedback: null,
    },
);

const feedbackIcon = computed(() =>
    props.feedback === "success" ? "check" : "warning",
);
</script>

<template>
    <button
        :type="nativeType"
        class="base-button"
        :class="[
            `is-${variant}`,
            `is-${size}`,
            { 'is-plain': plain },
            { 'is-block': block },
            { 'is-feedback': feedback },
        ]"
        :disabled="disabled || loading || !!feedback"
        :aria-busy="loading || undefined"
        v-bind="$attrs"
    >
        <span
            v-if="loading"
            class="base-button-spinner"
            aria-hidden="true"
        ></span>
        <span
            v-else-if="feedback"
            class="base-button-feedback"
            :class="`is-${feedback}`"
            aria-hidden="true"
        >
            <SvgIcon :name="feedbackIcon" size="sm" />
        </span>
        <span class="base-button-label"><slot /></span>
    </button>
</template>

<style scoped>
.base-button {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 42px;
    min-width: 96px;
    padding: 0 16px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-text-primary);
    font: inherit;
    font-size: 14px;
    font-weight: 700;
    line-height: 1;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    transition:
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

/* 键盘焦点（鼠标点击不显示，仅 Tab 聚焦时清晰可见） */
.base-button:focus-visible {
    outline: 2px solid var(--color-border-focus);
    outline-offset: 2px;
    box-shadow: 0 0 0 4px var(--color-focus-ring);
}

.base-button:hover:not(:disabled) {
    transform: translateY(-1px);
}

.base-button:active:not(:disabled) {
    transform: scale(0.98);
}

.base-button:disabled {
    cursor: not-allowed;
    opacity: 0.55;
}

/* 操作结果反馈仍锁定交互，但不把整颗按钮（含 check/warning 图标）变暗 */
.base-button.is-feedback:disabled {
    cursor: default;
    opacity: 1;
    pointer-events: none;
}

/* === 实心主色变体 === */
.base-button.is-primary {
    border-color: var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
}

.base-button.is-primary:hover:not(:disabled) {
    border-color: var(--color-primary-700);
    background: linear-gradient(
        135deg,
        var(--color-primary-700),
        var(--color-primary-600)
    );
    box-shadow: 0 8px 18px var(--color-focus-ring);
}

.base-button.is-danger {
    border-color: var(--color-danger);
    background: var(--color-danger);
    color: var(--color-text-on-primary);
}

.base-button.is-danger:hover:not(:disabled) {
    border-color: color-mix(in srgb, var(--color-danger) 84%, black);
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--color-danger) 84%, black),
        var(--color-danger)
    );
    box-shadow: 0 8px 18px var(--color-danger-soft);
}

.base-button.is-warning {
    border-color: var(--color-warning);
    background: var(--color-warning);
    color: var(--color-text-on-primary);
}

.base-button.is-warning:hover:not(:disabled) {
    border-color: color-mix(in srgb, var(--color-warning) 82%, black);
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--color-warning) 82%, black),
        var(--color-warning)
    );
    box-shadow: 0 8px 18px color-mix(in srgb, var(--color-warning) 24%, transparent);
}

/* === 文字按钮 === */
.base-button.is-text {
    border-color: transparent;
    background: transparent;
    color: var(--color-text-tertiary);
    min-width: 0;
}

.base-button.is-text:hover:not(:disabled) {
    color: var(--color-text-secondary);
}

/* === 尺寸 === */
.base-button.is-sm {
    height: 34px;
    min-width: 72px;
    padding: 0 12px;
    font-size: 13px;
    gap: 4px;
}

/* === 占满父容器宽度 === */
.base-button.is-block {
    width: 100%;
}

/* === 描边（plain）按钮：透明底 + 按变体着色，hover 填充柔和底色 === */
.base-button.is-plain {
    background: transparent;
    border-color: var(--color-primary-600);
    color: var(--color-primary-600);
}

.base-button.is-plain.is-primary {
    background: transparent;
    border-color: var(--color-primary-600);
    color: var(--color-primary-600);
}

.base-button.is-plain.is-danger {
    border-color: var(--color-danger);
    color: var(--color-danger);
}

.base-button.is-plain.is-warning {
    border-color: var(--color-warning);
    color: var(--color-warning);
}

.base-button.is-plain:hover:not(:disabled) {
    background: var(--color-primary-50);
    border-color: var(--color-primary-700);
    color: var(--color-primary-700);
    box-shadow: none;
}

.base-button.is-plain.is-primary:hover:not(:disabled) {
    background: var(--color-primary-50);
    border-color: var(--color-primary-700);
    color: var(--color-primary-700);
    box-shadow: none;
}

.base-button.is-plain.is-danger:hover:not(:disabled) {
    background: var(--color-danger-soft);
    border-color: color-mix(in srgb, var(--color-danger) 82%, black);
    box-shadow: none;
}

.base-button.is-plain.is-warning:hover:not(:disabled) {
    background: var(--color-warning-soft);
    border-color: color-mix(in srgb, var(--color-warning) 82%, black);
    box-shadow: none;
}

/* === Loading 旋转指示器 === */
.base-button-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 600ms linear infinite;
}

/* === 操作结果反馈：check/warning 一次性弹出 === */
.base-button-feedback {
    display: grid;
    place-items: center;
    animation: button-feedback-in 260ms var(--motion-ease-out) 1 both;
}

.base-button-feedback.is-success {
    color: var(--color-success);
}

.base-button-feedback.is-error {
    color: var(--color-danger);
}

@keyframes button-feedback-in {
    0% { transform: scale(0.4); opacity: 0; }
    60% { transform: scale(1.15); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
}
</style>