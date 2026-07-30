<script setup lang="ts">
import { computed } from "vue";
import { statusColorMap } from "../../constants/status-colors";
import type { DeviceStatus } from "../../types/animation";
import type { SemanticStatus } from "../../types/theme";

const props = defineProps<{
    status: DeviceStatus;
    label: string;
}>();

const semanticStatus = computed<SemanticStatus>(() => props.status);
const statusColors = computed(() => statusColorMap[semanticStatus.value]);
</script>

<template>
    <span class="inline-flex items-center gap-1.5">
        <span
            class="h-2 w-2 rounded-full transition-colors"
            :class="[
                statusColors.dotClass,
                { 'status-dot-running': status === 'running' },
            ]"
        ></span>
        <Transition name="status-crossfade" mode="out-in">
            <span :key="label">{{ label }}</span>
        </Transition>
    </span>
</template>
