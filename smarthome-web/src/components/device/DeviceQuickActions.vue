<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

const actions = [
    { key: "scan", label: "扫描新设备", tone: "primary", icon: "scan" },
    { key: "delete", label: "批量删除", tone: "danger", icon: "delete" },
    { key: "firmware", label: "固件更新", tone: "purple", icon: "firmware" },
    { key: "logs", label: "查看日志", tone: "warning", icon: "log" },
] as const;

defineEmits<{
    action: [key: (typeof actions)[number]["key"]];
}>();
</script>

<template>
    <section class="device-side-card">
        <h2>快捷操作</h2>
        <div class="quick-grid">
            <button
                v-for="item in actions"
                :key="item.key"
                :class="`is-${item.tone}`"
                type="button"
                @click="$emit('action', item.key)"
            >
                <span aria-hidden="true" class="tone-chip" :class="`is-${item.tone}`">
                    <SvgIcon :name="item.icon" />
                </span>
                {{ item.label }}
            </button>
        </div>
    </section>
</template>

<style scoped>
.device-side-card {
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 14px;
    box-shadow: var(--shadow-card);
}

h2 {
    margin: 0 0 12px;
    font-size: 16px;
    font-weight: 900;
}

.quick-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

button {
    display: grid;
    min-height: 76px;
    place-items: center;
    gap: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-panel-background);
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

button span {
    display: grid;
    width: 30px;
    height: 30px;
    place-items: center;
    border-radius: 9px;
}

button:hover {
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}
.is-primary:hover {
    border-color: var(--color-primary-300);
}
.is-success:hover {
    border-color: var(--color-success-border);
}
.is-warning:hover {
    border-color: var(--color-warning-border);
}
.is-danger:hover {
    border-color: var(--color-danger-border, #f56c6c);
}

.is-purple:hover {
    border-color: color-mix(in srgb, var(--tone-purple) 45%, var(--color-border-default));
}

button:active {
    transform: scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
    button {
        transition-duration: 1ms;
    }

    button:hover,
    button:active {
        transform: none;
    }
}
</style>
