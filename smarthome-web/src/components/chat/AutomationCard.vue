<script setup lang="ts">
import { useHomeStore } from "../../stores/home";
import type { Automation } from "../../types/automation";
import BaseSwitch from "../BaseSwitch.vue";

defineProps<{
    automation: Automation;
}>();

const store = useHomeStore();
</script>

<template>
    <article
        class="motion-card rounded-lg border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-3 hover:bg-[var(--color-panel-secondary)]"
    >
        <div class="flex items-start justify-between gap-3">
            <div>
                <strong class="block text-sm text-slate-800">{{
                    automation.name
                }}</strong>
                <span class="mt-1 block text-xs text-slate-500">{{
                    automation.trigger
                }}</span>
            </div>
            <BaseSwitch
                :model-value="automation.enabled"
                small
                @update:model-value="store.toggleAutomation(automation.id)"
            />
        </div>
        <p class="mt-2 text-xs leading-5 text-slate-500">
            {{ automation.actions.join(" · ") }}
        </p>
    </article>
</template>
