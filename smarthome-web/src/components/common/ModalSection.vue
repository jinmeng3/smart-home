<script setup lang="ts">
withDefaults(
    defineProps<{
        title?: string;
        description?: string;
    }>(),
    {
        title: "",
        description: "",
    },
);
</script>

<template>
    <section class="smart-modal-section">
        <header v-if="title || description" class="smart-modal-section-header">
            <h3 v-if="title">{{ title }}</h3>
            <p v-if="description">{{ description }}</p>
        </header>
        <slot />
    </section>
</template>

<style scoped>
.smart-modal-section {
    min-width: 0;
    border: 1px solid var(--color-border-default);
    border-radius: 16px;
    padding: 18px;
    background: var(--color-surface-subtle);
    transition:
        border-color 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease),
        transform 180ms var(--motion-ease);
}

.smart-modal-section:hover {
    border-color: var(--color-primary-200);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}

.smart-modal-section-header {
    margin-bottom: 14px;
}

.smart-modal-section-header h3 {
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 800;
    line-height: 1.25;
}

.smart-modal-section-header p {
    margin-top: 4px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    line-height: 1.5;
}

@media (prefers-reduced-motion: reduce) {
    .smart-modal-section {
        transition-duration: 1ms;
    }

    .smart-modal-section:hover {
        transform: none;
    }
}
</style>
