<script setup lang="ts">
import type { Room } from "../../types/room";
import RoomEditorDialog from "./dialogs/RoomEditorDialog.vue";
import RoomLogsDialog from "./dialogs/RoomLogsDialog.vue";
import RoomSceneDialog from "./dialogs/RoomSceneDialog.vue";
import RoomDevicesDialog from "./dialogs/RoomDevicesDialog.vue";
import RoomEnvironmentDialog from "./dialogs/RoomEnvironmentDialog.vue";

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
    create: [room: Pick<Room, "name" | "floor" | "roomType">];
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
