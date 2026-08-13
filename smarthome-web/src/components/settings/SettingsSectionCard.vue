<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    id: string;
    icon: string;
    title: string;
    tone?: string;
}>();
</script>

<template>
    <section
        :id="id"
        class="settings-section motion-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-4"
        :class="`tone-border-${tone ?? 'primary'}`"
    >
        <div class="mb-4 flex items-center gap-3">
            <span
                class="section-icon tone-chip"
                :class="`is-${tone ?? 'primary'}`"
            >
                <SvgIcon :name="icon" />
            </span>
            <h2 class="text-xl font-extrabold text-[var(--color-text-primary)]">
                {{ title }}
            </h2>
        </div>
        <slot />
    </section>
</template>

<style scoped>
.section-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: none;
    place-items: center;
    border-radius: 10px;
}

.settings-section {
    min-width: 0;
    box-shadow: var(--shadow-card);
}
</style>
