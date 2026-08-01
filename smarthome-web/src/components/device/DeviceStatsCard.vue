<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    label: string;
    value: number;
    tone: "success" | "muted" | "warning" | "primary";
    delay: number;
    icon: string;
}>();
</script>

<template>
    <article
        class="device-stats-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4 shadow-soft"
        :class="`is-${tone}`"
        :style="{ animationDelay: `${delay}ms` }"
    >
        <span class="device-stats-icon" aria-hidden="true">
            <SvgIcon :name="icon" size="lg" />
        </span>
        <div>
            <p class="text-sm font-semibold text-[var(--color-text-tertiary)]">
                {{ label }}
            </p>
            <strong class="mt-1 block text-2xl font-extrabold">{{ value }}</strong>
        </div>
    </article>
</template>

<style scoped>
.device-stats-card {
    display: grid;
    grid-template-columns: 48px minmax(0, 1fr);
    gap: 14px;
    align-items: center;
    animation: device-card-enter 220ms var(--motion-ease) both;
    transition:
        transform 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease);
}

.device-stats-card:hover {
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}

.device-stats-icon {
    display: grid;
    width: 48px;
    height: 48px;
    place-items: center;
    border-radius: 999px;
}

.is-success .device-stats-icon { background: var(--color-success-soft); }
.is-muted .device-stats-icon { background: var(--color-surface-subtle); }
.is-warning .device-stats-icon { background: var(--color-warning-soft); }
.is-primary .device-stats-icon { background: var(--color-primary-100); }
.is-success strong { color: var(--color-success); }
.is-muted strong { color: var(--color-text-secondary); }
.is-warning strong { color: var(--color-warning); }
.is-primary strong { color: var(--color-primary-600); }

@keyframes device-card-enter {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: reduce) {
    .device-stats-card {
        animation-duration: 1ms;
        animation-delay: 0ms !important;
        transition-duration: 1ms;
    }

    .device-stats-card:hover {
        transform: none;
    }
}
</style>
