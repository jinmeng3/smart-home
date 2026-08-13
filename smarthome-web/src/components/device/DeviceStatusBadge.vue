<script setup lang="ts">
import { computed } from "vue";
import type { DeviceStatus } from "../../types/device";
import { deviceStatusLabelMap } from "./deviceMeta";

const props = withDefaults(
    defineProps<{
        status: DeviceStatus;
        /** 尺寸：sm（小标签） / md（默认） */
        size?: "sm" | "md";
        /** 是否显示状态点 */
        showDot?: boolean;
        /** 是否显示文案 */
        showLabel?: boolean;
    }>(),
    {
        size: "md",
        showDot: true,
        showLabel: true,
    },
);
</script>

<template>
    <span
        class="dsb"
        :class="[
            `is-${status}`,
            `is-${size}`,
        ]"
    >
        <i
            v-if="showDot"
            class="dsb-dot"
            :class="`is-${status}`"
        ></i>
        <span v-if="showLabel" class="dsb-label">{{ deviceStatusLabelMap[status] }}</span>
    </span>
</template>

<style scoped>
.dsb {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    font-weight: 800;
    line-height: 1.4;
}

.dsb.is-sm {
    padding: 2px 7px;
    font-size: 11px;
}

.dsb.is-md {
    padding: 3px 10px;
    font-size: 12px;
}

.dsb-dot {
    width: 7px;
    height: 7px;
    flex: 0 0 7px;
    border-radius: 999px;
    background: currentColor;
}

.dsb.is-online {
    color: var(--color-success);
    background: var(--color-success-soft);
}

.dsb.is-offline {
    color: var(--color-text-muted);
    background: var(--color-surface-subtle);
}

.dsb.is-warning {
    color: var(--color-warning);
    background: var(--color-warning-soft);
}

.dsb.is-running {
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}
</style>