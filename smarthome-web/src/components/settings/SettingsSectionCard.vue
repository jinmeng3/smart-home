<script setup lang="ts">
defineProps<{
    id: string;
    icon: string;
    title: string;
}>();
</script>

<template>
    <section
        :id="id"
        class="settings-section motion-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
    >
        <div class="mb-4 flex items-center gap-3">
            <span
                class="grid h-9 w-9 place-items-center rounded-lg bg-[var(--color-ai-soft)] text-[var(--color-ai)]"
                >{{ icon }}</span
            >
            <h2 class="text-xl font-extrabold text-[var(--color-text-primary)]">
                {{ title }}
            </h2>
        </div>
        <slot />
    </section>
</template>

<style scoped>
.settings-section {
    content-visibility: auto;
    contain-intrinsic-size: 320px;
}
</style>
