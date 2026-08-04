<script setup lang="ts">
import type { SettingsSectionId } from "../../types/settings";

defineProps<{
    activeSection: SettingsSectionId;
}>();

const emit = defineEmits<{
    select: [section: SettingsSectionId];
}>();

const tabs: Array<{ id: SettingsSectionId; label: string }> = [
    { id: "account", label: "账户" },
    { id: "appearance", label: "界面" },
    { id: "ai", label: "智能助手" },
    { id: "homeAssistant", label: "平台接入" },
    { id: "notifications", label: "通知" },
    { id: "security", label: "安全" },
    { id: "backup", label: "备份恢复" },
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
            :class="{
                'bg-gradient-to-b from-[var(--color-primary-50)] to-[var(--color-primary-100)] text-[var(--color-primary-700)] shadow-sm':
                    activeSection === tab.id,
            }"
            type="button"
            @click="emit('select', tab.id)"
        >
            {{ tab.label }}
        </button>
    </nav>
</template>
