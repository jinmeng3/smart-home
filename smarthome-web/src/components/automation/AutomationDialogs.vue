<script setup lang="ts">
import AutomationFormDialog, {
    type AutomationRule,
} from "./dialogs/AutomationFormDialog.vue";
import AutomationImportDialog from "./dialogs/AutomationImportDialog.vue";
import AutomationLogsDialog from "./dialogs/AutomationLogsDialog.vue";
import AutomationScheduleDialog from "./dialogs/AutomationScheduleDialog.vue";
import AutomationBatchDialog from "./dialogs/AutomationBatchDialog.vue";

export type { AutomationRule } from "./dialogs/AutomationFormDialog.vue";

export type AutomationDialog =
    | "create"
    | "edit"
    | "import"
    | "logs"
    | "schedule"
    | "batch"
    | null;

const props = defineProps<{
    modelValue: AutomationDialog;
    rule?: AutomationRule;
    rules: AutomationRule[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: AutomationDialog];
    save: [
        payload: {
            mode: "create" | "edit";
            name: string;
            description: string;
            trigger: string;
        },
    ];
    batch: [ids: number[]];
    imported: [count: number];
    scheduled: [
        payload: { weekdays: number[]; time: string; ruleIds: number[] },
    ];
}>();

const close = () => emit("update:modelValue", null);
</script>

<template>
    <AutomationFormDialog
        v-if="modelValue === 'create' || modelValue === 'edit'"
        :model-value="Boolean(modelValue)"
        :rule="rule"
        :mode="modelValue"
        @save="emit('save', $event)"
        @update:model-value="close"
    />
    <AutomationImportDialog
        v-else-if="modelValue === 'import'"
        :model-value="true"
        :rules="rules"
        @imported="emit('imported', $event)"
        @update:model-value="close"
    />
    <AutomationLogsDialog
        v-else-if="modelValue === 'logs'"
        :model-value="true"
        @update:model-value="close"
    />
    <AutomationScheduleDialog
        v-else-if="modelValue === 'schedule'"
        :model-value="true"
        :rules="rules"
        @scheduled="emit('scheduled', $event)"
        @update:model-value="close"
    />
    <AutomationBatchDialog
        v-else-if="modelValue === 'batch'"
        :model-value="true"
        :rules="rules"
        @batch="emit('batch', $event)"
        @update:model-value="close"
    />
</template>
