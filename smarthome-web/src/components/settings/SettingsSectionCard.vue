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
    >
        <div class="mb-4 flex items-center gap-3">
            <span
                class="section-icon"
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
    background: var(--color-primary-100);
    color: var(--color-primary-700);
}

.section-icon.is-success {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.section-icon.is-teal {
    background: var(--color-teal-soft);
    color: var(--color-teal-600);
}
.section-icon.is-purple {
    background: color-mix(in srgb, #8b5cf6 14%, transparent);
    color: #8b5cf6;
}
.section-icon.is-indigo {
    background: color-mix(in srgb, #6366f1 14%, transparent);
    color: #6366f1;
}
.section-icon.is-orange {
    background: color-mix(in srgb, #ff8a1f 14%, transparent);
    color: #ff8a1f;
}
.section-icon.is-warning {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}
.section-icon.is-danger {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}
</style>
