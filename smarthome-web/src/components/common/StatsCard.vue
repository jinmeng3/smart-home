<script setup lang="ts">
import SvgIcon from "./SvgIcon.vue";

defineProps<{
    icon: string;
    label: string;
    value: string | number;
    unit?: string;
    detail?: string;
    tone: string;
}>();
</script>

<template>
    <article class="stats-card" :class="tone">
        <i><SvgIcon :name="icon" /></i>
        <span>
            {{ label }}
            <strong>{{ value }}<small v-if="unit">{{ unit }}</small></strong>
            <em v-if="detail">{{ detail }}</em>
        </span>
    </article>
</template>

<style scoped>
.stats-card {
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px 16px;
    transition:
        transform 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease);
}

.stats-card:hover {
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}

.stats-card i {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    color: var(--color-primary-700);
    background: var(--color-primary-100);
}

.stats-card.blue i {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
}

.stats-card.green i {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.stats-card.orange i {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.stats-card.purple i {
    background: var(--color-secondary-soft);
    color: var(--color-secondary-600);
}

.stats-card.red i {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.stats-card span {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.stats-card strong {
    display: flex;
    align-items: baseline;
    gap: 2px;
    color: var(--color-text-primary);
    font-size: 22px;
    font-weight: 900;
    letter-spacing: -0.01em;
}

.stats-card strong small {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.stats-card em {
    font-style: normal;
    font-size: 12px;
    color: var(--color-text-tertiary);
}

.stats-card.green em {
    color: var(--color-success);
}

.stats-card.orange em {
    color: var(--color-warning);
}

@media (prefers-reduced-motion: reduce) {
    .stats-card {
        transition-duration: 1ms;
    }

    .stats-card:hover {
        transform: none;
    }
}
</style>