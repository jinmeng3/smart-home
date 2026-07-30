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
        class="flex h-12 shrink-0 items-center gap-6 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] px-5"
    >
        <button
            v-for="tab in tabs"
            :key="tab.id"
            class="motion-button relative h-full text-sm font-semibold text-[var(--color-text-secondary)] hover:text-[var(--color-primary-700)]"
            :class="{
                'text-[var(--color-primary-700)]': activeSection === tab.id,
            }"
            type="button"
            @click="emit('select', tab.id)"
        >
            {{ tab.label }}
            <span
                v-if="activeSection === tab.id"
                class="absolute bottom-0 left-0 h-0.5 w-full rounded-full bg-[var(--color-primary-600)]"
            ></span>
        </button>
    </nav>
</template>
