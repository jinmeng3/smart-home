<script setup lang="ts">
withDefaults(
    defineProps<{
        variant?: "default" | "primary" | "danger" | "text";
        size?: "sm" | "md";
        plain?: boolean;
        loading?: boolean;
        disabled?: boolean;
        nativeType?: "button" | "submit" | "reset";
    }>(),
    {
        variant: "default",
        size: "md",
        plain: false,
        loading: false,
        disabled: false,
        nativeType: "button",
    },
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
        ]"
        :disabled="disabled || loading"
        v-bind="$attrs"
    >
        <span
            v-if="loading"
            class="base-button-spinner"
            aria-hidden="true"
        ></span>
        <span class="base-button-label"><slot /></span>
    </button>
</template>

<style scoped>
.base-button {
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
    cursor: pointer;
    user-select: none;
    transition:
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
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

.base-button.is-text {
    border-color: transparent;
    background: transparent;
    color: var(--color-text-tertiary);
    min-width: 0;
}

.base-button.is-sm {
    height: 34px;
    min-width: 72px;
    padding: 0 12px;
    font-size: 13px;
    gap: 4px;
}

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

.base-button.is-plain.is-primary:hover:not(:disabled) {
    background: var(--color-primary-50);
    border-color: var(--color-primary-700);
    color: var(--color-primary-700);
    box-shadow: none;
}

.base-button.is-danger {
    border-color: var(--color-danger);
    background: var(--color-danger);
    color: var(--color-text-on-primary);
}

.base-button.is-danger:hover:not(:disabled) {
    border-color: #b91c1c;
    background: linear-gradient(
        135deg,
        #b91c1c,
        var(--color-danger)
    );
    box-shadow: 0 8px 18px var(--color-danger-soft);
}

.base-button-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: base-button-spin 600ms linear infinite;
}

@keyframes base-button-spin {
    to {
        transform: rotate(360deg);
    }
}
</style>