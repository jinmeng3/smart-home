<script setup lang="ts">
import SvgIcon from "./SvgIcon.vue";

withDefaults(
    defineProps<{
        title: string;
        description?: string;
        icon?: string;
        tone?: string;
        soft?: string;
    }>(),
    {
        description: "",
        icon: "",
        tone: "",
        soft: "",
    },
);
</script>

<template>
    <header class="page-header">
        <div class="page-title">
            <span
                v-if="icon"
                class="page-header-icon"
                :style="{
                    background: soft || 'var(--color-surface-subtle)',
                    color: tone || 'var(--color-text-tertiary)',
                }"
                aria-hidden="true"
            >
                <SvgIcon :name="icon" />
            </span>
            <div class="page-heading">
                <h1>{{ title }}</h1>
                <p v-if="description">{{ description }}</p>
            </div>
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

.page-title {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 12px;
}

.page-header-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    transition:
        background-color 180ms var(--motion-ease),
        color 180ms var(--motion-ease);
}

.page-heading {
    min-width: 0;
}

.page-heading h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 900;
    color: var(--color-text-primary);
    line-height: 1.15;
}

.page-heading p {
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

@media (max-width: 767px) {
    .page-header {
        gap: 12px;
    }

    .page-header-icon {
        width: 38px;
        height: 38px;
        flex-basis: 38px;
        border-radius: 10px;
    }

    .page-heading h1 {
        font-size: 20px;
    }

    .page-heading p {
        margin-top: 5px;
        font-size: 12px;
    }

    .page-actions {
        width: 100%;
        min-width: 0;
        flex-wrap: wrap;
    }
}
</style>
