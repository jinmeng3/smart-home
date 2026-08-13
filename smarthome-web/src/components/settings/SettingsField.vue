<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    label: string;
    description?: string;
    icon?: string;
    /** 图标色值标识，如 "danger"、"success"、"primary" */
    tone?: string;
    /** 垂直布局（标签在上，控件在下） */
    vertical?: boolean;
}>();
</script>

<template>
    <div
        class="sf-field"
        :class="{
            'is-vertical': vertical,
            [`tone-${tone}`]: tone,
        }"
    >
        <span v-if="icon" class="sf-icon" :class="tone ? `is-${tone}` : ''">
            <SvgIcon :name="icon" size="sm" />
        </span>
        <div class="sf-copy">
            <strong>{{ label }}</strong>
            <small v-if="description">{{ description }}</small>
        </div>
        <div class="sf-control">
            <slot />
        </div>
    </div>
</template>

<style scoped>
.sf-field {
    display: grid;
    min-height: 56px;
    grid-template-columns: 38px minmax(0, 1fr) auto;
    align-items: center;
    gap: 11px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-surface-subtle);
    padding: 10px 12px;
    transition:
        border-color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease);
}

.sf-field:hover {
    border-color: var(--color-border-default);
}

.sf-field.is-vertical {
    grid-template-columns: 1fr;
    min-height: auto;
    gap: 6px;
    padding: 14px;
}

.sf-icon {
    display: grid;
    width: 38px;
    height: 38px;
    place-items: center;
    border-radius: 10px;
    background: var(--color-surface-hover);
    color: var(--color-text-tertiary);
}

.sf-icon.is-primary { background: var(--color-primary-50); color: var(--color-primary-600); }
.sf-icon.is-danger { background: var(--color-danger-soft); color: var(--color-danger); }
.sf-icon.is-success { background: var(--color-success-soft); color: var(--color-success); }
.sf-icon.is-warning { background: var(--color-warning-soft); color: var(--color-warning); }
.sf-icon.is-indigo { background: var(--tone-indigo-soft); color: var(--tone-indigo); }
.sf-icon.is-orange { background: var(--tone-orange-soft); color: var(--tone-orange); }
.sf-icon.is-purple { background: var(--tone-purple-soft); color: var(--tone-purple); }

.sf-copy {
    display: grid;
    min-width: 0;
    gap: 2px;
}

.sf-copy strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 850;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sf-copy small {
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sf-control {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: flex-end;
}
</style>