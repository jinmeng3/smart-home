<script setup lang="ts">
import type { Room } from "../../types/room";
import { defineAsyncDialog } from "../../utils/asyncDialog";

const RoomEditorDialog = defineAsyncDialog(
    () => import("./dialogs/RoomEditorDialog.vue"),
);
const RoomLogsDialog = defineAsyncDialog(
    () => import("./dialogs/RoomLogsDialog.vue"),
);
const RoomSceneDialog = defineAsyncDialog(
    () => import("./dialogs/RoomSceneDialog.vue"),
);
const RoomDevicesDialog = defineAsyncDialog(
    () => import("./dialogs/RoomDevicesDialog.vue"),
);
const RoomEnvironmentDialog = defineAsyncDialog(
    () => import("./dialogs/RoomEnvironmentDialog.vue"),
);

export type RoomDialog =
    | "edit"
    | "create"
    | "logs"
    | "scene"
    | "devices"
    | "environment"
    | null;

defineProps<{
    modelValue: RoomDialog;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: RoomDialog];
    create: [room: {
        name: string;
        floor: string;
        roomType: string;
        icon: string;
        themeColor: string;
        deviceIds: number[];
    }];
    update: [room: Room];
}>();

const close = () => emit("update:modelValue", null);
</script>

<template>
    <RoomEditorDialog
        v-if="modelValue === 'edit' || modelValue === 'create'"
        :model-value="Boolean(modelValue)"
        :room="room"
        :mode="modelValue"
        @create="emit('create', $event)"
        @update="emit('update', $event)"
        @update:model-value="close"
    />
    <RoomLogsDialog
        v-else-if="modelValue === 'logs'"
        :model-value="true"
        :room="room"
        @update:model-value="close"
    />
    <RoomSceneDialog
        v-else-if="modelValue === 'scene'"
        :model-value="true"
        :room="room"
        @update:model-value="close"
    />
    <RoomDevicesDialog
        v-else-if="modelValue === 'devices'"
        :model-value="true"
        :room="room"
        @update:model-value="close"
    />
    <RoomEnvironmentDialog
        v-else-if="modelValue === 'environment'"
        :model-value="true"
        :room="room"
        @update:model-value="close"
    />
</template>
