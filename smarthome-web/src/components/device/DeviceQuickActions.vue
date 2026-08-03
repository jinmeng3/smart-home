<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

const actions = [
    { key: "scan", label: "扫描新设备", tone: "primary", icon: "scan" },
    { key: "group", label: "批量分组", tone: "success", icon: "group" },
    { key: "firmware", label: "固件更新", tone: "primary", icon: "firmware" },
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
                <span aria-hidden="true">
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
    min-height: 72px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
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
    width: 24px;
    height: 24px;
    place-items: center;
    border-radius: 8px;
}

.is-primary span {
    background: var(--color-primary-100);
}
.is-success span {
    background: var(--color-success-soft);
}
.is-warning span {
    background: var(--color-warning-soft);
}

button:hover {
    border-color: var(--color-primary-300);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-1px);
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
