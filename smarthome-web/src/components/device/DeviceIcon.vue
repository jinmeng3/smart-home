<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import { getDeviceTypeIcon } from "./deviceMeta";
import type { DeviceStatus } from "../../types/device";

interface DeviceLike {
    icon?: string;
    type: string;
    color?: string;
    status?: DeviceStatus;
}

const props = withDefaults(
    defineProps<{
        device: DeviceLike;
        size?: "sm" | "md" | "lg";
        /** 离线时降低饱和度 */
        dimOffline?: boolean;
        /** 显示颜色背景 */
        showBackground?: boolean;
    }>(),
    {
        size: "md",
        dimOffline: true,
        showBackground: true,
    },
);

const iconName = computed(() =>
    getDeviceTypeIcon(props.device.icon || props.device.type),
);

const shouldDim = computed(
    () => props.dimOffline && props.device.status === "offline",
);
</script>

<template>
    <span
        class="di"
        :class="[
            `is-${size}`,
            {
                'is-dimmed': shouldDim,
                'has-bg': showBackground,
            },
        ]"
        :style="showBackground && device.color ? { '--di-color': device.color } : undefined"
        aria-hidden="true"
    >
        <SvgIcon :name="iconName" />
    </span>
</template>

<style scoped>
.di {
    display: grid;
    place-items: center;
    border-radius: 10px;
    flex: 0 0 auto;
    color: var(--color-text-tertiary);
}

.di.has-bg {
    background: color-mix(
        in srgb,
        var(--di-color, var(--color-primary-500)) 12%,
        transparent
    );
    color: var(--di-color, var(--color-primary-600));
}

.di.is-sm {
    width: 24px;
    height: 24px;
    border-radius: 7px;
}

.di.is-md {
    width: 32px;
    height: 32px;
    border-radius: 9px;
}

.di.is-lg {
    width: 44px;
    height: 44px;
    border-radius: 12px;
}

.di.is-dimmed {
    opacity: 0.5;
    filter: grayscale(0.6);
}
</style>