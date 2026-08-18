<script setup lang="ts">
withDefaults(
    defineProps<{
        tone?: string;
        title?: string;
        description?: string;
    }>(),
    {
        tone: "",
        title: "",
        description: "",
    },
);
</script>

<template>
    <section
        class="smart-modal-section"
        :style="tone ? { '--section-tone': tone } : undefined"
    >
        <header v-if="title || description" class="smart-modal-section-header">
            <h3 v-if="title" :class="{ 'has-tone': tone }">{{ title }}</h3>
            <p v-if="description">{{ description }}</p>
        </header>
        <slot />
    </section>
</template>

<style scoped>
.smart-modal-section {
    min-width: 0;
    border: 1px solid
        color-mix(in srgb, var(--section-tone, var(--color-primary-600)) 16%, var(--color-border-subtle));
    border-radius: 13px;
    background: var(--color-card-bg);
    padding: 14px;
}

.smart-modal-section-header {
    margin-bottom: 12px;
}

.smart-modal-section-header h3 {
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
    line-height: 1.3;
}

.smart-modal-section-header h3.has-tone {
    color: var(--section-tone);
}

.smart-modal-section-header p {
    margin-top: 3px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    line-height: 1.5;
}
</style>