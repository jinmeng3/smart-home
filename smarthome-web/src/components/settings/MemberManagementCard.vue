<script setup lang="ts">
import { computed, ref } from "vue";
import { ElButton, ElDialog, ElMessage } from "element-plus";
import type { FamilyMember, MemberRole } from "../../types/account";
import SettingsSectionCard from "./SettingsSectionCard.vue";
import MemberListItem from "./MemberListItem.vue";
import "element-plus/theme-chalk/el-dialog.css";
import "element-plus/theme-chalk/el-overlay.css";

const props = defineProps<{
    adminCount: number;
    canManage: boolean;
    currentMemberId: number | null;
    loadingMemberId: number | null;
    members: FamilyMember[];
    submitting: boolean;
}>();

const emit = defineEmits<{
    addMember: [email: string, role: MemberRole];
    removeMember: [id: number];
    updateMemberRole: [id: number, role: MemberRole];
}>();

const memberEmail = ref("");
const memberRole = ref<MemberRole>("member");
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

const updateMemberRole = (member: FamilyMember, role: MemberRole) => {
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
    <SettingsSectionCard id="members" icon="▣" title="家庭成员与权限">
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
                当前权限：{{ currentMember?.role === "admin" ? "管理员" : "成员" }}
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

    <ElDialog
        v-model="dialogVisible"
        :close-on-click-modal="!submitting && loadingMemberId === null"
        :close-on-press-escape="!submitting && loadingMemberId === null"
        :lock-scroll="true"
        :modal="true"
        :show-close="false"
        append-to-body
        class="member-management-dialog"
        modal-class="settings-dialog-overlay"
        width="720px"
    >
        <template #header>
            <header class="dialog-header">
                <span class="dialog-icon" aria-hidden="true">▣</span>
                <div>
                    <h2>家庭成员与权限</h2>
                    <p>查看家庭成员，并管理每位成员的访问权限</p>
                </div>
                <ElButton
                    aria-label="关闭"
                    class="close-button"
                    :disabled="submitting || loadingMemberId !== null"
                    text
                    @click="dialogVisible = false"
                    >×</ElButton
                >
            </header>
        </template>

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
                    {{ canManage ? "管理员可调整角色或移除普通成员" : readonlyMessage }}
                </span>
                <ElButton @click="dialogVisible = false">完成</ElButton>
            </footer>
        </template>
    </ElDialog>
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

:global(.member-management-dialog) {
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 20px;
    background: var(--color-panel-background);
    box-shadow: 0 24px 70px rgb(15 23 42 / 22%);
}

:global(.settings-dialog-overlay) {
    background: var(--color-overlay);
    backdrop-filter: blur(4px);
}

:global(.member-management-dialog .el-dialog__header),
:global(.member-management-dialog .el-dialog__body),
:global(.member-management-dialog .el-dialog__footer) {
    padding: 0;
}

.dialog-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 17px 20px 14px;
    border-bottom: 1px solid var(--color-divider);
    background: linear-gradient(
        135deg,
        var(--color-dialog-header-start),
        var(--color-dialog-header-end)
    );
}

.dialog-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 11px;
    color: white;
    background: linear-gradient(
        135deg,
        var(--color-dialog-icon-start),
        var(--color-dialog-icon-end)
    );
}

.dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 17px;
    font-weight: 800;
}

.dialog-header p {
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}

.close-button {
    margin: -4px -6px 0 auto;
    color: var(--color-text-tertiary);
    font-size: 22px;
}

.member-toolbar {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 112px 84px;
    gap: 8px;
    padding: 16px 20px 12px;
}

.member-list {
    display: grid;
    max-height: 390px;
    gap: 8px;
    overflow-y: auto;
    padding: 0 20px 18px;
}

.dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 20px;
    border-top: 1px solid var(--color-divider);
    background: var(--color-workspace-background);
}

.dialog-footer span {
    color: var(--color-text-tertiary);
    font-size: 11px;
}

@media (max-width: 640px) {
    :global(.member-management-dialog) {
        width: calc(100% - 24px) !important;
    }

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
