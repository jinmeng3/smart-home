<script setup lang="ts">
import type { SettingsSuggestionItem } from "../../types/settings";
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    suggestions: SettingsSuggestionItem[];
}>();

const emit = defineEmits<{
    select: [target: SettingsSuggestionItem["target"]];
}>();
</script>

<template>
    <section
        class="motion-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-5"
    >
        <div class="mb-4 flex items-center gap-3">
            <span
                class="grid h-9 w-9 place-items-center rounded-lg bg-[var(--color-warning-soft)] text-[var(--color-warning)]"
            >
                <SvgIcon name="settings" size="sm" />
            </span>
            <h2 class="text-base font-extrabold">设置建议</h2>
        </div>
        <div class="grid gap-3">
            <button
                v-for="item in suggestions"
                :key="item.id"
                class="motion-button grid grid-cols-[36px_minmax(0,1fr)_auto] items-center gap-3 rounded-lg p-3 text-left hover:bg-[var(--color-surface-subtle)]"
                type="button"
                @click="emit('select', item.target)"
            >
                <span
                    class="grid h-9 w-9 place-items-center rounded-full bg-[var(--color-primary-50)] text-[var(--color-primary-600)]"
                >
                    <SvgIcon name="ai" size="sm" />
                </span>
                <span class="min-w-0">
                    <strong class="block truncate text-sm">{{
                        item.title
                    }}</strong>
                    <span
                        class="block truncate text-xs text-[var(--color-text-tertiary)]"
                        >{{ item.description }}</span
                    >
                </span>
                <SvgIcon
                    class="text-[var(--color-text-tertiary)]"
                    name="chevron-right"
                    size="sm"
                />
            </button>
        </div>
    </section>
</template>
