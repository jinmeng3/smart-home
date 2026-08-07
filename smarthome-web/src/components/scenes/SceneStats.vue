<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";

const props = defineProps<{
    enabled: number;
    automation: number;
    manual: number;
    monthlyExecutions: number;
    enabledRate: number;
    automationRate: number;
    manualRate: number;
    monthlyGrowthRate: number;
}>();

const formatRate = (value: number) => `${Math.round(value)}%`;

const noteFor = computed(() => (key: string) => {
    switch (key) {
        case "enabled":
            return `${formatRate(props.enabledRate)} 场景已启用`;
        case "automation":
            return `占比 ${formatRate(props.automationRate)}`;
        case "manual":
            return `占比 ${formatRate(props.manualRate)}`;
        case "monthlyExecutions":
            return `较上月 ${formatRate(props.monthlyGrowthRate)}`;
        default:
            return "";
    }
});

const items = [
    {
        key: "enabled",
        label: "已启用场景",
        icon: "check-circle",
        tone: "primary",
    },
    {
        key: "automation",
        label: "自动化场景",
        icon: "automation",
        tone: "success",
    },
    {
        key: "manual",
        label: "手动场景",
        icon: "power",
        tone: "warning",
    },
    {
        key: "monthlyExecutions",
        label: "本月执行次数",
        icon: "log",
        tone: "info",
    },
] as const;
</script>

<template>
    <div class="scene-stats-grid">
        <article
            v-for="(item, index) in items"
            :key="item.key"
            class="scene-stat-card"
            :class="`is-${item.tone}`"
            :style="{ animationDelay: `${index * 55}ms` }"
        >
            <span class="scene-stat-icon"><SvgIcon :name="item.icon" /></span>
            <div>
                <p>{{ item.label }}</p>
                <strong>{{ $props[item.key] }}</strong>
                <small>{{ noteFor(item.key) }}</small>
            </div>
        </article>
    </div>
</template>

<style scoped>
.scene-stats-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
}

.scene-stat-card {
    display: grid;
    grid-template-columns: 48px minmax(0, 1fr);
    gap: 13px;
    align-items: center;
    min-height: 94px;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 15px 18px;
    box-shadow: var(--shadow-card);
    animation: scene-card-enter 220ms var(--motion-ease) both;
    transition:
        transform 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease);
}

.scene-stat-card:hover {
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}

.scene-stat-icon {
    display: grid;
    width: 48px;
    height: 48px;
    place-items: center;
    border-radius: 999px;
}

p,
small {
    margin: 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 800;
}

strong {
    display: block;
    margin: 3px 0;
    color: var(--color-text-primary);
    font-size: 24px;
    font-weight: 900;
    line-height: 1;
}

.is-primary .scene-stat-icon {
    color: var(--color-primary-600);
    background: var(--color-primary-100);
}
.is-success .scene-stat-icon {
    color: var(--color-success);
    background: var(--color-success-soft);
}
.is-warning .scene-stat-icon {
    color: var(--color-warning);
    background: var(--color-warning-soft);
}
.is-info .scene-stat-icon {
    color: var(--color-info);
    background: var(--color-info-soft);
}
.is-info small {
    color: var(--color-success);
}

@keyframes scene-card-enter {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 1180px) {
    .scene-stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (prefers-reduced-motion: reduce) {
    .scene-stat-card {
        animation-duration: 1ms;
        animation-delay: 0ms !important;
        transition-duration: 1ms;
    }

    .scene-stat-card:hover {
        transform: none;
    }
}
</style>
