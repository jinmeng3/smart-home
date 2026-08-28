<script setup lang="ts">
const model = defineModel<boolean>({ required: true });

defineProps<{
    disabled?: boolean;
    small?: boolean;
}>();
</script>

<template>
    <button
        :aria-checked="model"
        :class="{ active: model, small }"
        :disabled="disabled"
        class="base-switch"
        role="switch"
        type="button"
        @click="model = !model"
    >
        <span />
    </button>
</template>

<style scoped>
.base-switch {
    position: relative;
    width: 40px;
    height: 22px;
    flex: 0 0 auto;
    border-radius: 999px;
    background: var(--color-border-default);
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    transition: background-color 160ms var(--motion-ease);
}

/* 键盘焦点可见性 */
.base-switch:focus-visible {
    outline: 2px solid var(--color-border-focus);
    outline-offset: 2px;
    box-shadow: 0 0 0 4px var(--color-focus-ring);
}

.base-switch span {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    transition: transform 160ms var(--motion-ease);
}

.base-switch.active {
    background: var(--color-primary-600);
}

.base-switch.active span {
    transform: translateX(18px);
}

.base-switch:disabled {
    cursor: not-allowed;
    opacity: 0.5;
}

.base-switch.small {
    width: 34px;
    height: 18px;
}

.base-switch.small span {
    top: 2px;
    left: 2px;
    width: 14px;
    height: 14px;
}

.base-switch.small.active span {
    transform: translateX(16px);
}
</style>
