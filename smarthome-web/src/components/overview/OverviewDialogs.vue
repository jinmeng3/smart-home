<script setup lang="ts">
import ModeDialog from "./dialogs/ModeDialog.vue";
import RoomDialog from "./dialogs/RoomDialog.vue";
import InspectionDialog from "./dialogs/InspectionDialog.vue";
import DevicesDialog from "./dialogs/DevicesDialog.vue";
import ScheduleDialog from "./dialogs/ScheduleDialog.vue";
import SyncDialog from "./dialogs/SyncDialog.vue";

export type OverviewDialog =
    | "mode"
    | "room"
    | "inspection"
    | "devices"
    | "schedule"
    | "sync"
    | null;

defineProps<{
    modelValue: OverviewDialog;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: OverviewDialog];
    synced: [];
    "room-created": [name: string];
}>();

const close = () => emit("update:modelValue", null);
</script>

<template>
    <ModeDialog
        v-if="modelValue === 'mode'"
        :model-value="true"
        @update:model-value="close"
    />
    <RoomDialog
        v-else-if="modelValue === 'room'"
        :model-value="true"
        @update:model-value="close"
        @room-created="emit('room-created', $event)"
    />
    <InspectionDialog
        v-else-if="modelValue === 'inspection'"
        :model-value="true"
        @update:model-value="close"
    />
    <DevicesDialog
        v-else-if="modelValue === 'devices'"
        :model-value="true"
        @update:model-value="close"
    />
    <ScheduleDialog
        v-else-if="modelValue === 'schedule'"
        :model-value="true"
        @update:model-value="close"
    />
    <SyncDialog
        v-else-if="modelValue === 'sync'"
        :model-value="true"
        @update:model-value="close"
        @synced="emit('synced')"
    />
</template>
