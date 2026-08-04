<script setup lang="ts">
import type { SettingsSectionId } from "../../types/settings";

defineProps<{
    activeSection: SettingsSectionId;
}>();

const emit = defineEmits<{
    select: [section: SettingsSectionId];
}>();

const tabs: Array<{ id: SettingsSectionId; label: string; tone: string }> = [
    { id: "account", label: "账户", tone: "blue" },
    { id: "appearance", label: "界面", tone: "teal" },
    { id: "ai", label: "智能助手", tone: "purple" },
    { id: "homeAssistant", label: "平台接入", tone: "orange" },
    { id: "notifications", label: "通知", tone: "amber" },
    { id: "security", label: "安全", tone: "red" },
    { id: "backup", label: "备份恢复", tone: "sky" },
];
</script>

<template>
    <nav
        class="flex h-12 shrink-0 items-center gap-1.5 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-1.5"
    >
        <button
            v-for="tab in tabs"
            :key="tab.id"
            class="motion-button relative grid flex-1 place-items-center whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-primary-700)]"
            :class="[
                { active: activeSection === tab.id },
                `is-${tab.tone}`,
            ]"
            type="button"
            @click="emit('select', tab.id)"
        >
            {{ tab.label }}
        </button>
    </nav>
</template>

<style scoped>
button.active {
    box-shadow: 0 1px 2px rgb(16 24 40 / 0.08);
}

.is-blue.active {
    background: linear-gradient(to bottom, var(--color-primary-50), var(--color-primary-100));
    color: var(--color-primary-700);
}
.is-teal.active {
    background: linear-gradient(
        to bottom,
        var(--color-teal-soft),
        color-mix(in srgb, var(--color-teal-soft) 45%, var(--color-teal-600))
    );
    color: var(--color-teal-600);
}
.is-purple.active {
    background: linear-gradient(
        to bottom,
        color-mix(in srgb, #8b5cf6 10%, transparent),
        color-mix(in srgb, #8b5cf6 18%, transparent)
    );
    color: #8b5cf6;
}
.is-orange.active {
    background: linear-gradient(
        to bottom,
        color-mix(in srgb, #ff8a1f 10%, transparent),
        color-mix(in srgb, #ff8a1f 18%, transparent)
    );
    color: #ff8a1f;
}
.is-amber.active {
    background: linear-gradient(
        to bottom,
        var(--color-warning-soft),
        color-mix(in srgb, var(--color-warning-soft) 40%, var(--color-warning))
    );
    color: var(--color-warning);
}
.is-red.active {
    background: linear-gradient(
        to bottom,
        var(--color-danger-soft),
        color-mix(in srgb, var(--color-danger-soft) 45%, var(--color-danger))
    );
    color: var(--color-danger);
}
.is-sky.active {
    background: linear-gradient(
        to bottom,
        var(--color-info-soft),
        color-mix(in srgb, var(--color-info-soft) 45%, var(--color-info))
    );
    color: var(--color-info);
}
</style>
