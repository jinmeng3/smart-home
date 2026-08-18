<script setup lang="ts">
import { computed } from "vue";
import { MorphIcon } from "morphicons/vue";
import type { IconInput, SpringPreset } from "morphicons";
import { getIcon } from "../../constants/iconRegistry";

const props = withDefaults(
    defineProps<{
        name: string;
        size?: "sm" | "md" | "lg";
        label?: string;
    }>(),
    {
        size: "md",
        label: undefined,
    },
);

/** 尺寸映射：sm=16px, md=20px, lg=24px（与 .orion-icon CSS 契约一致） */
const iconSize = computed(() => {
    switch (props.size) {
        case "sm":
            return 16;
        case "lg":
            return 24;
        default:
            return 20;
    }
});

const resolvedIcon = computed<IconInput>(() => getIcon(props.name));

/** 统一的 spring 参数，morphicons 预设之一 */
const spring: SpringPreset = "snappy";
</script>

<template>
    <MorphIcon
        :icon="resolvedIcon"
        :size="iconSize"
        :stroke-width="1.8"
        :reduced-motion="'user'"
        :spring="spring"
        :label="label"
        class="orion-icon"
        :class="`is-${size}`"
    />
</template>

<style scoped>
.orion-icon {
    display: inline-block;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    color: currentColor;
    vertical-align: middle;
}

.orion-icon.is-sm {
    width: 16px;
    height: 16px;
}

.orion-icon.is-lg {
    width: 24px;
    height: 24px;
}
</style>