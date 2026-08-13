<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

export interface RailAction {
    key: string;
    label: string;
    tone: string;
    icon: string;
}

const props = withDefaults(
    defineProps<{
        actions: RailAction[];
        /** 布局：网格（2 列）或横向行 */
        layout?: "grid" | "row";
        /** 正在同步的操作 key（用于图标旋转/禁用） */
        syncingKey?: string;
    }>(),
    {
        layout: "grid",
        syncingKey: "",
    },
);

const emit = defineEmits<{
    action: [key: string];
}>();
</script>

<template>
    <section class="rail-actions">
        <h3 class="rail-section-title">快捷操作</h3>
        <div class="rail-actions-grid" :class="`is-${props.layout}`">
            <button
                v-for="item in actions"
                :key="item.key"
                :class="`is-${item.tone}`"
                type="button"
                :disabled="syncingKey === item.key"
                @click="emit('action', item.key)"
            >
                <span aria-hidden="true" class="rail-action-icon">
                    <SvgIcon
                        :class="{ 'is-spinning': syncingKey === item.key }"
                        :name="item.icon"
                        size="sm"
                    />
                </span>
                {{ item.label }}
            </button>
        </div>
    </section>
</template>

<style scoped>
.rail-actions {
    border: 1px solid var(--color-border-subtle);
    border-radius: 14px;
    background: var(--color-panel-background);
    padding: 13px;
    box-shadow: var(--shadow-card);
}

.rail-section-title {
    margin: 0 0 10px;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 900;
}

.rail-actions-grid {
    display: grid;
    gap: 8px;
}

.rail-actions-grid.is-grid {
    grid-template-columns: 1fr 1fr;
}

.rail-actions-grid.is-row {
    display: flex;
    flex-wrap: wrap;
}

.rail-actions-grid.is-row button {
    flex: 1 1 auto;
    min-width: 64px;
}

.rail-actions-grid button {
    display: inline-flex;
    min-height: 34px;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 9px;
    background: var(--color-panel-secondary);
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
    padding: 0 8px;
    transition:
        background-color 120ms var(--motion-ease),
        border-color 120ms var(--motion-ease),
        transform 90ms ease;
}

.rail-actions-grid button:hover {
    background: var(--color-surface-hover);
    border-color: var(--color-border-default);
    color: var(--color-text-primary);
    transform: translateY(0);
}

.rail-actions-grid button:active {
    transform: scale(0.98);
}

.rail-actions-grid button:disabled {
    opacity: 0.6;
    cursor: default;
}

.rail-actions-grid button svg {
    transition: color 120ms ease;
}

.rail-action-icon {
    display: grid;
    width: 24px;
    height: 24px;
    place-items: center;
    border-radius: 7px;
    background: var(--color-surface-subtle);
}

button.is-primary .rail-action-icon { color: var(--color-primary-600); }
button.is-danger .rail-action-icon { color: var(--color-danger); }
button.is-warning .rail-action-icon { color: var(--color-warning); }
button.is-purple .rail-action-icon { color: var(--tone-purple); }
button.is-success .rail-action-icon { color: var(--color-success); }

svg.is-spinning {
    animation: rail-action-spin 800ms linear infinite;
}

@keyframes rail-action-spin {
    to {
        transform: rotate(360deg);
    }
}

@media (prefers-reduced-motion: reduce) {
    .rail-actions-grid button,
    .rail-actions-grid button:active {
        transform: none;
    }

    svg.is-spinning {
        animation-duration: 1.5s;
    }
}
</style>
