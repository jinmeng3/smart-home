<script setup lang="ts">
defineProps<{
    title: string;
    description?: string;
}>();
</script>

<template>
    <header class="page-header">
        <div class="page-title">
            <h1>{{ title }}</h1>
            <p v-if="description">{{ description }}</p>
        </div>
        <div class="page-actions">
            <slot />
        </div>
    </header>
</template>

<style scoped>
.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
}

.page-title h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 900;
    color: var(--color-text-primary);
    line-height: 1.15;
}

.page-title p {
    margin: 8px 0 0;
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 700;
}

.page-actions {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 8px;
}

@media (max-width: 1180px) {
    .page-header {
        display: grid;
    }
}
</style>