<script setup lang="ts">
import ModeDialog from "./dialogs/ModeDialog.vue";
import RoomDialog from "./dialogs/RoomDialog.vue";
import InspectionDialog from "./dialogs/InspectionDialog.vue";
import ScheduleDialog from "./dialogs/ScheduleDialog.vue";
import SyncDialog from "./dialogs/SyncDialog.vue";
import RoomDistributionDialog from "./dialogs/RoomDistributionDialog.vue";
import ActivityDialog from "./dialogs/ActivityDialog.vue";
import type { HouseholdSchedule } from "../../api/overview";

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
