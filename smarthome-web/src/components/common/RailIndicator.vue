<script setup lang="ts">
import SvgIcon from "./SvgIcon.vue";

withDefaults(
    defineProps<{
        icon: string;
        /** 图标语义色：success / warning / danger / primary / teal / purple / muted */
        tone?: string;
        /** 状态点：布尔或状态名（online/warning/offline/running） */
        dot?: boolean | string;
        active?: boolean;
        /** 角标数字/文本，0 或空则不显示 */
        badge?: number | string;
        tooltip?: string;
    }>(),
    {
        tone: "muted",
        dot: false,
        active: false,
        badge: undefined,
        tooltip: "",
    },
);
</script>

<template>
    <span
        class="ri"
        :class="{
            'is-active': active,
            [`is-${tone}`]: tone,
        }"
        :title="tooltip || undefined"
        :aria-label="tooltip || undefined"
    >
        <SvgIcon :name="icon" size="sm" />
        <i
            v-if="dot"
            class="ri-dot"
            :class="typeof dot === 'string' ? `is-${dot}` : ''"
        ></i>
        <span
            v-if="badge !== undefined && badge !== 0 && badge !== ''"
            class="ri-badge"
            >{{ badge }}</span
        >
    </span>
</template>

<style scoped>
.ri {
    position: relative;
    display: grid;
    width: 34px;
    height: 34px;
    place-items: center;
    border-radius: 10px;
    background: var(--color-surface-hover);
    color: var(--color-text-tertiary);
    transition:
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.ri.is-success { color: var(--color-success); }
.ri.is-warning { color: var(--color-warning); }
.ri.is-danger { color: var(--color-danger); }
.ri.is-primary { color: var(--color-primary-600); }
.ri.is-teal { color: var(--color-teal-600); }
.ri.is-purple { color: var(--tone-purple); }
.ri.is-indigo { color: var(--tone-indigo); }
.ri.is-orange { color: var(--tone-orange); }
.ri.is-muted { color: var(--color-text-muted); }

.ri.is-active {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.ri-dot {
    position: absolute;
    right: -1px;
    bottom: -1px;
    width: 9px;
    height: 9px;
    border-radius: 999px;
    border: 2px solid var(--color-rail-bg, var(--color-workspace-background));
    background: var(--color-text-muted);
}

.ri-dot.is-online { background: var(--color-success); }
.ri-dot.is-warning { background: var(--color-warning); }
.ri-dot.is-offline { background: var(--color-text-muted); }
.ri-dot.is-running { background: var(--color-primary-500); }

.ri-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    display: grid;
    min-width: 16px;
    height: 16px;
    place-items: center;
    border-radius: 999px;
    border: 2px solid var(--color-rail-bg, var(--color-workspace-background));
    background: var(--color-danger);
    color: #fff;
    font-size: 9px;
    font-weight: 900;
    padding: 0 3px;
    box-sizing: content-box;
}
</style>