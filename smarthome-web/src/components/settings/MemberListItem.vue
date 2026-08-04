<script setup lang="ts">
import type { FamilyMember, HouseholdRole } from "../../types/settings";

defineProps<{
    canEdit: boolean;
    canRemove: boolean;
    member: FamilyMember;
    roleLoading: boolean;
    removeLoading: boolean;
}>();

const emit = defineEmits<{
    remove: [id: number];
    updateRole: [id: number, role: HouseholdRole];
}>();
</script>

<template>
    <div
        class="grid min-h-[54px] grid-cols-[32px_minmax(0,1fr)_104px_70px] items-center gap-3 rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-panel-background)] px-3 py-2"
    >
        <img
            v-if="member.avatarUrl"
            class="h-8 w-8 rounded-full object-cover"
            :src="member.avatarUrl"
            alt=""
        />
        <span
            v-else
            class="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-blue-100 to-blue-600 text-sm font-extrabold text-white"
        >
            {{ member.name.slice(0, 1) }}
        </span>
        <span class="min-w-0">
            <strong
                class="block truncate text-sm text-[var(--color-text-primary)]"
                >{{ member.name }}</strong
            >
            <span
                class="block truncate text-xs text-[var(--color-text-tertiary)]"
                >{{ member.email }}</span
            >
        </span>
        <select
            class="settings-input w-full px-2"
            :disabled="!canEdit || roleLoading"
            :value="member.role"
            @change="
                emit(
                    'updateRole',
                    member.id,
                    ($event.target as HTMLSelectElement).value as HouseholdRole,
                )
            "
        >
            <option value="admin">管理员</option>
            <option value="member">成员</option>
        </select>
        <button
            class="secondary-button min-w-0 px-2"
            :disabled="!canRemove || removeLoading"
            type="button"
            @click="emit('remove', member.id)"
        >
            {{ removeLoading ? "移除中" : "移除" }}
        </button>
    </div>
</template>
