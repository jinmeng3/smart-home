<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

withDefaults(
    defineProps<{
        visible: boolean;
        label?: string;
    }>(),
    {
        label: "正在刷新",
    },
);
</script>

<template>
    <div v-if="visible" class="cro" role="status" aria-live="polite">
        <div class="cro-spinner" aria-hidden="true"></div>
        <span>{{ label }}</span>
    </div>
</template>

<style scoped>
.cro {
    position: absolute;
    inset: 0;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: color-mix(in srgb, var(--color-card-bg) 72%, transparent);
    backdrop-filter: blur(2px);
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    animation: cro-fade-in 160ms ease;
}

.cro-spinner {
    width: 26px;
    height: 26px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: cro-spin 600ms linear infinite;
}

@keyframes cro-fade-in {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@media (prefers-reduced-motion: reduce) {
    .cro {
        animation: none;
    }
}
</style>