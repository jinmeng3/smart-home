<script setup lang="ts">
import SvgIcon from "./SvgIcon.vue";

defineProps<{
    icon: string;
    title: string;
    description?: string;
    tone?: string;
    color?: string;
}>();
</script>

<template>
    <div class="confirm-entity-summary">
        <span
            class="confirm-entity-icon"
            :class="tone"
            :style="color ? { '--confirm-entity-color': color } : undefined"
            aria-hidden="true"
        >
            <SvgIcon :name="icon" />
        </span>
        <div>
            <strong>{{ title }}</strong>
            <p v-if="description">{{ description }}</p>
            <slot />
        </div>
    </div>
</template>

<style scoped>
.confirm-entity-summary {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 18px;
    border: 1px solid var(--color-primary-200);
    border-radius: 14px;
    background: var(--color-primary-50);
}

.confirm-entity-icon {
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    border-radius: 50%;
    background: var(--confirm-entity-color, var(--color-primary-600));
    color: var(--color-text-on-primary);
}

.confirm-entity-summary > div {
    min-width: 0;
}

.confirm-entity-summary strong,
.confirm-entity-summary p {
    display: block;
    overflow: hidden;
    margin: 0;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.confirm-entity-summary strong {
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 800;
}

.confirm-entity-summary p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 13px;
}
</style>
