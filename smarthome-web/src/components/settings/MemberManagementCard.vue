<script setup lang="ts">
import { computed, ref } from "vue";
import { ElButton, ElMessage } from "element-plus";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import type { FamilyMember, HouseholdRole } from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import MemberListItem from "./MemberListItem.vue";

const props = defineProps<{
    adminCount: number;
    canManage: boolean;
    currentMemberId: number | null;
    loadingMemberId: number | null;
    members: FamilyMember[];
    submitting: boolean;
}>();

const emit = defineEmits<{
    addMember: [email: string, role: HouseholdRole];
    removeMember: [id: number];
    updateMemberRole: [id: number, role: HouseholdRole];
}>();

const memberEmail = ref("");
const memberRole = ref<HouseholdRole>("member");
const dialogVisible = ref(false);
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const readonlyMessage = computed(() =>
    props.canManage ? "" : "普通成员只能查看成员列表",
);
const currentMember = computed(() =>
    props.members.find((member) => member.id === props.currentMemberId),
);

const addMember = () => {
    const email = memberEmail.value.trim();

    if (!props.canManage) {
        ElMessage.warning(readonlyMessage.value);
        return;
    }

    if (!emailPattern.test(email)) {
        ElMessage.warning("请输入正确的成员邮箱");
        return;
    }

    if (
        props.members.some(
            (member) => member.email.toLowerCase() === email.toLowerCase(),
        )
    ) {
        ElMessage.error("该成员已存在");
        return;
    }

    emit("addMember", email, memberRole.value);
    memberEmail.value = "";
};

const canRemove = (member: FamilyMember) => {
    if (!props.canManage || member.id === props.currentMemberId) {
        return false;
    }

    return member.role === "member";
};

const updateMemberRole = (member: FamilyMember, role: HouseholdRole) => {
    if (!props.canManage) {
        ElMessage.warning(readonlyMessage.value);
        return;
    }

    if (member.role === "admin" && role === "member" && props.adminCount <= 1) {
        ElMessage.error("家庭至少保留一名管理员");
        return;
    }

    emit("updateMemberRole", member.id, role);
};
</script>

<template>
    <SettingsSectionCard id="members" icon="members" title="家庭成员与权限" tone="teal">
        <div class="member-summary">
            <div>
                <strong>{{ members.length }}</strong>
                <span>位家庭成员</span>
            </div>
            <div>
                <strong>{{ adminCount }}</strong>
                <span>位管理员</span>
            </div>
            <span class="role-badge">
                当前权限：{{
                    currentMember?.role === "admin" ? "管理员" : "成员"
                }}
            </span>
        </div>

        <button
            class="secondary-button mt-4 w-full"
            type="button"
            @click="dialogVisible = true"
        >
            {{ canManage ? "管理成员与权限" : "查看家庭成员" }}
        </button>
    </SettingsSectionCard>

    <BaseSmartModal
        v-model="dialogVisible"
        width="720px"
        :close-on-overlay="!submitting && loadingMemberId === null"
        title="家庭成员与权限"
        description="查看家庭成员，并管理每位成员的访问权限"
        icon="members"
        :close-button-disabled="submitting || loadingMemberId !== null"
    >
        <div class="member-toolbar">
            <input
                v-model="memberEmail"
                class="settings-input w-full"
                :disabled="!canManage || submitting"
                placeholder="成员邮箱"
            />
            <select
                v-model="memberRole"
                class="settings-input w-full px-2"
                :disabled="!canManage || submitting"
            >
                <option value="admin">管理员</option>
                <option value="member">成员</option>
            </select>
            <button
                class="secondary-button min-w-0 px-2"
                :disabled="!canManage || submitting"
                type="button"
                @click="addMember"
            >
                {{ submitting ? "添加中" : "添加" }}
            </button>
        </div>

        <p
            v-if="readonlyMessage"
            class="mb-3 text-xs font-medium text-[var(--color-text-tertiary)]"
        >
            {{ readonlyMessage }}
        </p>

        <div class="member-list">
            <MemberListItem
                v-for="member in members"
                :key="member.id"
                :can-edit="canManage"
                :can-remove="canRemove(member)"
                :member="member"
                :remove-loading="loadingMemberId === member.id"
                :role-loading="loadingMemberId === member.id"
                @remove="emit('removeMember', member.id)"
                @update-role="(_, role) => updateMemberRole(member, role)"
            />
            <div
                v-if="!members.length"
                class="rounded-lg border border-dashed border-[var(--color-border-default)] py-10 text-center text-sm text-[var(--color-text-tertiary)]"
            >
                暂无成员
            </div>
        </div>

        <template #footer>
            <footer class="dialog-footer">
                <span>
                    {{
                        canManage
                            ? "管理员可调整角色或移除普通成员"
                            : readonlyMessage
                    }}
                </span>
                <ElButton @click="dialogVisible = false">完成</ElButton>
            </footer>
        </template>
    </BaseSmartModal>
</template>

<style scoped>
.member-summary {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 88px)) 1fr;
    align-items: center;
    gap: 12px;
}

.member-summary > div {
    padding: 10px;
    border-radius: 11px;
    background: var(--color-workspace-background);
}

.member-summary strong,
.member-summary span {
    display: block;
}

.member-summary strong {
    color: var(--color-primary-600);
    font-size: 18px;
}

.member-summary div span {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

.role-badge {
    justify-self: end;
    padding: 6px 9px;
    border-radius: 999px;
    color: var(--color-primary-600);
    font-size: 11px;
    font-weight: 700;
    background: var(--color-ai-soft);
}

.member-toolbar {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 112px 84px;
    gap: 8px;
    margin: 0 0 16px;
    padding: 14px;
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.member-list {
    display: grid;
    max-height: 390px;
    gap: 8px;
    overflow-y: auto;
    padding: 0 20px 18px;
}

@media (max-width: 640px) {
    .member-toolbar {
        grid-template-columns: 1fr;
    }

    .member-summary {
        grid-template-columns: repeat(2, 1fr);
    }

    .role-badge {
        grid-column: 1 / -1;
        justify-self: start;
    }
}
</style>
