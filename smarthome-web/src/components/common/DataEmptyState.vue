<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    icon?: string;
    title: string;
    description?: string;
}>();

defineSlots<{
    default?: any;
}>();
</script>

<template>
    <div class="des">
        <SvgIcon v-if="icon" :name="icon" size="lg" />
        <strong>{{ title }}</strong>
        <small v-if="description">{{ description }}</small>
        <div v-if="$slots.default" class="des-actions">
            <slot />
        </div>
    </div>
</template>

<style scoped>
.des {
    display: grid;
    place-items: center;
    align-content: center;
    gap: 10px;
    min-height: 200px;
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 700;
}

.des svg {
    width: 40px;
    height: 40px;
    opacity: 0.4;
}

.des strong {
    font-size: 14px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}

.des small {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-muted);
}

.des-actions {
    display: flex;
    gap: 8px;
    margin-top: 4px;
}
</style>