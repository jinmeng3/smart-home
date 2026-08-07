<script setup lang="ts">
import type { HouseholdSchedule } from "../../api/overview";
import { defineAsyncDialog } from "../../utils/asyncDialog";

const ModeDialog = defineAsyncDialog(() => import("./dialogs/ModeDialog.vue"));
const RoomDialog = defineAsyncDialog(() => import("./dialogs/RoomDialog.vue"));
const InspectionDialog = defineAsyncDialog(
    () => import("./dialogs/InspectionDialog.vue"),
);
const ScheduleDialog = defineAsyncDialog(
    () => import("./dialogs/ScheduleDialog.vue"),
);
const SyncDialog = defineAsyncDialog(() => import("./dialogs/SyncDialog.vue"));
const RoomDistributionDialog = defineAsyncDialog(
    () => import("./dialogs/RoomDistributionDialog.vue"),
);
const ActivityDialog = defineAsyncDialog(
    () => import("./dialogs/ActivityDialog.vue"),
);

export type OverviewDialog =
    | "mode"
    | "room"
    | "inspection"
    | "schedule"
    | "sync"
    | "distribution"
    | "activity"
    | null;

interface RoomData {
    name: string;
    icon: string;
    count: number;
    light: string;
    air: string;
    extra: string;
    tone: string;
}

interface ActivityItem {
    time: string;
    icon: string;
    title: string;
    description: string;
    tone: string;
}

defineProps<{
    modelValue: OverviewDialog;
    rooms?: RoomData[];
    activities?: ActivityItem[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: OverviewDialog];
    synced: [];
    "room-created": [name: string];
    "schedule-saved": [value: HouseholdSchedule];
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
    <ScheduleDialog
        v-else-if="modelValue === 'schedule'"
        :model-value="true"
        @saved="emit('schedule-saved', $event)"
        @update:model-value="close"
    />
    <SyncDialog
        v-else-if="modelValue === 'sync'"
        :model-value="true"
        @update:model-value="close"
        @synced="emit('synced')"
    />
    <RoomDistributionDialog
        v-else-if="modelValue === 'distribution'"
        :model-value="true"
        :rooms="rooms ?? []"
        @update:model-value="close"
    />
    <ActivityDialog
        v-else-if="modelValue === 'activity'"
        :model-value="true"
        :activities="activities ?? []"
        @update:model-value="close"
    />
</template>
