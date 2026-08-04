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
                'tone-gradient',
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
</style>
