<script setup lang="ts">
import { computed } from "vue";
import { useHomeStore } from "../../stores/home";
import type { Automation } from "../../types/automation";
import BaseSwitch from "../BaseSwitch.vue";
import SvgIcon from "../common/SvgIcon.vue";

const props = defineProps<{
    automation: Automation;
}>();

const store = useHomeStore();

const automationMeta = computed(() => {
    const map: Record<string, { icon: string; tone: string }> = {
        "wake-up": { icon: "illumination", tone: "orange" },
        "arrive-home": { icon: "home", tone: "blue" },
        sleep: { icon: "scene", tone: "purple" },
    };

    return map[props.automation.id] ?? { icon: "clock", tone: "teal" };
});
</script>

<template>
    <article
        class="motion-card rounded-lg border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-3 hover:bg-[var(--color-panel-secondary)]"
    >
        <div class="flex items-start justify-between gap-3">
            <div class="flex min-w-0 items-start gap-3">
                <span
                    class="automation-icon"
                    :class="`is-${automationMeta.tone}`"
                    aria-hidden="true"
                >
                    <SvgIcon :name="automationMeta.icon" size="sm" />
                </span>
                <div class="min-w-0">
                    <strong
                        class="block truncate text-sm text-[var(--color-text-primary)]"
                        >{{ automation.name }}</strong
                    >
                    <span
                        class="mt-1 block truncate text-xs text-[var(--color-text-tertiary)]"
                        >{{ automation.trigger }}</span
                    >
                </div>
            </div>
            <BaseSwitch
                :model-value="automation.enabled"
                small
                @update:model-value="store.toggleAutomation(automation.id)"
            />
        </div>
        <p
            class="mt-2 truncate text-xs leading-5 text-[var(--color-text-tertiary)]"
        >
            {{ automation.actions.join(" · ") }}
        </p>
    </article>
</template>

<style scoped>
.automation-icon {
    display: grid;
    width: 34px;
    height: 34px;
    flex: none;
    place-items: center;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    color: var(--color-primary-700);
}

.automation-icon.is-blue {
    background: var(--color-info-soft);
    color: var(--color-device-climate);
}

.automation-icon.is-orange {
    background: var(--color-warning-soft);
    color: var(--color-device-light);
}

.automation-icon.is-purple {
    background: var(--color-device-camera-soft);
    color: var(--color-device-camera);
}

.automation-icon.is-teal {
    background: var(--color-teal-soft);
    color: var(--color-teal-600);
}
</style>
